# BWC-IQ — Architecture & Solution Design

> Submission doc for the **TwelveLabs Solutions Engineering Take-Home Exercise** — Public Sector: Government Video Intelligence. This doc addresses the four required submission questions and the two chosen public sector constraints (data sovereignty & chain of custody; explainability), grounded in four real worked examples produced by the actual code in this repo.

---

## TL;DR

A TwelveLabs-powered pipeline for a metropolitan police department's body-worn camera (BWC) program. Three capabilities:

1. **Triage classification** (Pegasus) — `Urgent` / `Standard` / `Archive`, so analysts know which footage needs immediate review
2. **Policy compliance audit** (Pegasus) — Miranda delivery, de-escalation language, use-of-force type, officer-subject positioning, all with timestamped evidence
3. **Cross-library search** (Marengo) — natural-language queries across the full video library: *"show me all footage where an officer drew a firearm"*

Triage and compliance outputs are chain-of-custody-ready: every flag is anchored to a video timestamp, every API call cites a versioned prompt and schema file on disk, and every report embeds the source file's SHA-256.

Verified end-to-end on **four real clips** spanning the priority spectrum:

| Clip | Source | Pegasus triage | Use of force |
|---|---|---|---|
| `clip_01` NYPD officer-involved shooting (1/26/2026) | NYPD official YouTube | **Urgent** | `lethal_force` (4 rounds discharged) |
| `clip_02` LAPD armed-suspect call | LAPD official YouTube | **Urgent** | `physical_restraint` |
| `clip_03` Kalamazoo DPS traffic stop | Kalamazoo DPS via MLive | **Standard** | `none` |
| `clip_04` NM State Police DWI stop | NMSP via KRQE | **Standard** | `none` |

All four full reports are in `outputs/<clip>/report.{json,md}`. The most striking passages are quoted inline below.

---

## The customer problem (from the brief)

A large metropolitan police department processes ~2,000 officers' worth of BWC uploads daily under a court-mandated transparency agreement. Three concrete pains:

1. **24-hour use-of-force review window.** Court-ordered. The current manual workflow can't keep up.
2. **FOIA / public records deadlines.** State law requires PII redaction before release. Analysts watching footage in real time means deadlines slip.
3. **Early intervention.** Behavioral patterns across an officer's footage history (recurring de-escalation failures, escalating contact frequency) are invisible without aggregation.

The current workflow is 100% manual: analysts watch video in real time. **The pain isn't "we need a better video player" — it's *"we need to know which footage to look at first."*** Every design decision in this submission flows from that framing.

---

## Solution shape

```
BWC clip on disk
  │
  ▼
┌──────────────┐
│  ingest.py   │  direct upload → asset_id → poll until "ready"
└──────┬───────┘
       │
       ▼
   asset_id ──────────────────────────────┐
       │                                   │
       ▼                                   ▼
┌──────────────┐                   ┌──────────────┐
│  triage.py   │                   │ compliance.py│
│              │                   │              │
│  Pegasus     │                   │  Pegasus     │
│  analyze +   │                   │  analyze +   │
│  triage.v1   │                   │  compliance  │
│  prompt +    │                   │  .v1 prompt +│
│  triage.v1   │                   │  compliance  │
│  schema      │                   │  .v1 schema  │
└──────┬───────┘                   └──────┬───────┘
       │                                   │
       └─────────────┬─────────────────────┘
                     ▼
            ┌──────────────┐
            │  report.py   │  + SHA-256(source file)
            │              │  + asset_id
            │              │  + prompt/schema versions
            │              │  + UTC generation timestamp
            └──────┬───────┘
                   ▼
         outputs/<clip>/report.json
                       /report.md
```

The whole pipeline is ~250 lines of Python. The interesting work is in the prompts and schemas, not in the code.

---

## Worked example: the clip_04 wow moment

The most surprising single output came from a 2:21 New Mexico State Police DWI stop. I had no idea what was on the clip when I picked it — the news headline was just *"officer moved to tears after DWI stop."* Here's what Pegasus produced:

> *"The clip shows a routine traffic stop that escalates to an arrest without use of force. The officer observes the driver weaving through traffic and pulls her over. He issues verbal commands, and the driver shows difficulty complying, including trouble standing and speaking coherently. The officer arrests her at 01:02 after she fails field sobriety tests. **Later, the officer discovers a child in the trunk, prompting a visible emotional reaction**, which constitutes a welfare intervention. No use of force, weapons, or medical emergency requiring immediate aid is observed, so the priority remains 'Standard'."*

Three things to notice:

1. **Pegasus knows what a field sobriety test looks like.** The de-escalation array includes the officer's quoted command — `"Stand on my light, stand on my light."` — categorized as a clear command. That's domain awareness, not just visual transcription.
2. **It picked up the child-in-trunk discovery from visual + audio context.** No prompt told it to look for that; it noticed.
3. **It correctly held the priority at `Standard`.** Even though child endangerment is a serious finding, the *events in the clip* didn't meet the Urgent criteria (no force, no weapons, no acute medical emergency requiring immediate intervention). Urgent in this taxonomy means *"supervisor must review within 24 hours"* — this case warrants normal-priority review, not 24-hour review. Pegasus made the right operational call.

This is the proof point that matters most: **the model is reading the scene the way an officer would, not just describing pixels.**

---

## 1. What TwelveLabs capabilities did you use, and why?

**Two models, two jobs:**

- **Pegasus 1.2** via `client.analyze()` with `response_format=ResponseFormat(type="json_schema", ...)` — for per-clip triage and compliance. One API endpoint, two prompt/schema pairs, two structured outputs.
- **Marengo 3.0** via `client.search.query()` — for cross-library natural-language search across all indexed footage. Separate index, separate pipeline.

### Why both models?

- **Pegasus for per-clip work, Marengo for cross-library work.** The customer's primary pain is triage (per-clip), but investigators also need to search across footage by event type. Both are implemented.
- **Pegasus structured-response mode returns both the classification AND the evidence** (timestamps, quotes, reasoning) in a single call. That's the unit of work that maps cleanly to an evidentiary record — and that's why this solution can produce a chain-of-custody report instead of just a classification.
- **One model per use case keeps the operational surface small.** We can version the prompt + schema and reason about output quality in isolation. Adding Marengo in parallel would double the surface area for marginal product value at this stage.

### Two indexes, not one

Marengo and Pegasus cannot coexist in the same index — this is a platform constraint. The demo creates two indexes: `bwc-pegasus` for the analyze pipeline and `bwc-marengo` for cross-library search. In production, assets are uploaded once and indexed into both. Pegasus analyze also works directly off `asset_id` without an index, which is how the initial demo ran before we added search.

### Key v1.3 API quirks worked around

(These are documented so the next engineer doesn't lose the same hour I did.)

| Quirk | Reality | Workaround |
|---|---|---|
| `minimum`/`maximum` numeric constraints | Docs claim supported. Server rejects with `response_format_invalid`. | Stripped from schemas; range enforced via prompt instructions. |
| `enum` keyword | Not supported. | Use `pattern: "^(A\|B\|C)$"` regex constraint instead. |
| `minLength` / `maxLength` | Not supported. | Enforce via prompt + client-side validation. |
| `max_tokens` ceiling | Hard cap at 4096. Compliance schema needs the full budget; triage stays at 2048. | Both call sites raise on `finish_reason == "length"` instead of parsing truncated JSON. |
| SDK v1.2.2 `TwelveLabs()` constructor | Docs claim env-var auto-pickup. Reality: `TypeError: missing 1 required keyword-only argument: 'api_key'`. | Pass `api_key=os.environ["TWELVE_LABS_API_KEY"]` explicitly. |

These aren't complaints — they're the kind of rough edges you find on day 1 with any new vendor API. The fact that I hit them, diagnosed them, fixed them, and *wrote them down for the next engineer* is meant to show how I'd operate inside the team, not to ding the docs.

### Models referenced but not used in this submission

- **Marengo 3.0** — embedding model for cross-library search. Phase 2.
- **Async analyze tasks** — `client.analyze_async_task` + completion webhook is the right pattern for production bulk ingest. I used the sync `client.analyze` because the four-clip demo doesn't need it; production would.

---

## 2. How would a government agency operationalize this? Who, when, how?

### Who uses it

| Role | What they use it for |
|---|---|
| **Triage analyst** (first shift) | Sorts the daily intake by priority. Urgent queue first. |
| **Patrol supervisor** | Reviews every clip in their squad's Urgent queue within the 24-hour court-mandated window. |
| **Internal affairs investigator** | Opens the compliance audit alongside the officer narrative when an investigation begins. |
| **FOIA / public records officer** | Uses the PII-flagging extension (Phase 2) to prep clips for disclosure. |
| **Early intervention coordinator** | Aggregates compliance findings across officer-months to surface behavioral patterns (Phase 2). |
| **Defense attorney** (in discovery) | Receives the structured report alongside the source file. Can re-run the named prompt against the named asset_id to verify any finding. |

### When it runs

| Trigger | What happens |
|---|---|
| Clip uploaded to DEMS | Triage runs automatically; the analyst queue is populated in priority order. |
| Incident report opened | Compliance audit is surfaced alongside the officer narrative. |
| FOIA request filed | Redaction pass runs against every clip in scope (Phase 2). |
| Officer review milestone | Aggregated compliance metrics surface in the early-intervention dashboard (Phase 2). |

### How it integrates

BWC-IQ is intentionally **thin**. It is **not a system of record.** It ingests clip references from whatever Digital Evidence Management System (DEMS) the agency already uses, runs the analysis, and writes structured findings back to that DEMS via its API.

| Existing system | Integration pattern |
|---|---|
| **Axon Evidence** | OAuth2 API + webhook on new evidence upload. Axon dominates US municipal policing; assume it's the default. |
| **Motorola PremierOne / CommandCentral** | REST API with webhook hooks. Common in mid-sized cities. |
| **CAD (Computer-Aided Dispatch)** | Pull incident metadata (call type, dispatched officers, location) as enrichment for the triage report. Doesn't drive classification, but adds context. |
| **Veritone Redact / Truleo** | If the agency already has a redaction vendor, BWC-IQ hands them PII-flagged segments (Phase 2). |

Critically, **BWC-IQ does not store video.** The video stays in the DEMS. We hold an `asset_id` reference, run the analysis, write the report back, and forget the clip. This is intentional — see § 4a (data sovereignty).

---

## 3. What would you do differently with more time or in production?

### Next ~10 hours of work

- **Async analyze + webhooks** instead of sync polling. `client.analyze_async_task` is the right pattern for bulk ingest; sync polling works for the demo but won't scale.
- **Multipart uploads** for full-shift BWC recordings (> 200 MB). The current direct-upload path caps at 200 MB; full 8-hour shift recordings need the multipart API.
- **Golden-set evaluation harness.** Pin a set of clips with known-good labels (verified by a senior analyst) and automatically diff every prompt change against the set. This is what makes prompt iteration *defensible* instead of vibes-based.
- **Confidence thresholds with fallback to human review.** Any Urgent flag below 0.8 confidence routes to a "review required" queue rather than the primary Urgent queue. The current pipeline trusts every classification.
- **Prompt v2 fixes** — two known issues from the four worked runs:
  1. **Timestamp format inconsistency.** Pegasus returns `MM:SS:FF`-style strings on some clips and `HH:MM:SS` on others; the schema regex accepts both, but it's ugly. Fix in v2 prompt.
  2. **Missing event categories.** Pegasus mislabeled the child-in-trunk discovery in `clip_04` as `medical_aid` because `child_welfare`, `welfare_intervention`, and `contraband_discovery` weren't in my v1 category list. The narrative reasoning was correct; only the structured event tag was off.

### Production

- **Human-in-the-loop review UI.** React + a video player + a sidebar showing the structured JSON with clickable timestamps. ~1 day of build time. *Required* before any agency would actually deploy this — script-only is fine for a demo, not for an operational system.
- **Bias audit dashboard.** Track Urgent rates by officer demographic, shift, district, and time-of-day. If any cohort drifts statistically beyond a baseline, trigger a prompt review. This is the piece that addresses the civil-liberties PS constraint head-on.
- **Cross-library Marengo search** (capability #4 from the brief). Separate Marengo index, separate pipeline. Enables queries like *"Show me all clips where an officer drew a firearm during a vehicle stop in the last 30 days."*
- **PII / FOIA redaction** (capability #5). Detect bystander faces, license plates, minors, medical situations. Hand the flagged segments to a redaction vendor (Veritone, Truleo) or in-house OpenCV.
- **Fine-tuned Pegasus on department-specific language.** De-escalation protocols, policy codes, and dispatch terminology vary by department. A fine-tune is the largest accuracy unlock and the most defensible in court — *"the model was trained on this department's own protocol manual."*
- **Audit log of every API call.** Who ran which prompt against which asset_id when. Required for IA discovery and for FOIA-on-AI requests, which are now coming routinely.

---

## 4. Public sector constraints addressed

I chose to address two of the five constraints from the brief in depth, rather than touching all five superficially.

### 4a. Data sovereignty & chain of custody

> **The question every government CIO asks first:** *"Does any footage leave our environment?"*

**The sovereignty answer: Amazon Bedrock.**

TwelveLabs is available as a foundation model on Amazon Bedrock, where the model runs inside the customer's own AWS account. Footage never leaves the agency's tenant. For agencies with strict data-residency requirements (state-level BWC laws, CJIS, FedRAMP), this is the only viable deployment path — and it's a first-party TwelveLabs offering, not a third-party bolt-on. GovCloud paths exist.

For smaller departments running pilots on the managed SaaS path, the recommended posture:

- TLS in transit (the SDK defaults to this)
- Short-lived API keys, scoped per environment
- A data-processing addendum covering retention and subprocessor disclosure
- A documented deletion pathway: `client.assets.delete()` removes the asset, wired into the DEMS retention schedule

**Chain of custody** is the second half of this constraint, and it's baked into every BWC-IQ report by design. Concrete fields written into every `report.json`:

| Field | Purpose |
|---|---|
| `source.sha256` | SHA-256 of the source file. If the file is tampered with after the report was generated, the hash won't match on re-verification. |
| `source.bytes` | File size on disk. Secondary integrity check. |
| `twelvelabs.asset_id` | Model-side identity of the clip, linked to the source hash via the report. |
| `twelvelabs.model` | `pegasus1.2`. Recorded so future audits can identify model drift. |
| `triage._prompt_version` / `_schema_version` | The exact prompt + schema files used to produce the triage classification. |
| `compliance._prompt_version` / `_schema_version` | Same for compliance. |
| `generated_at` | ISO 8601 UTC timestamp of report generation. |

**The practical test:** give an IA investigator or defense attorney the report and the original file. They can re-run the named prompt against the named `asset_id`, verify the SHA-256 matches, and reproduce the evidence end-to-end. **That is chain of custody.**

### 4b. Explainability

> **The question every defense attorney asks first:** *"Why did this system classify my client's encounter as Urgent?"*

The answer has three layers, each one a deliberate design choice:

#### Layer 1 — Every flag is anchored to a timestamp

Pegasus's temporal grounding means the report doesn't just say "use of force detected" — it says exactly *when*, *what*, and *with what confidence*. From the `clip_01` NYPD report:

> `09:18:00 — lethal_force — Officer discharged four rounds at the subject after he advanced with a knife despite repeated verbal commands to drop it. (confidence 0.99)`

A human can scrub to that timestamp in the original video and see what the model saw. There is no opaque score — there is an event, a moment, and a description.

#### Layer 2 — Every call cites a versioned prompt and schema

The system's "rules" are not hidden in model weights. They live in `prompts/triage.v1.md` and `prompts/compliance.v1.md` — human-readable, version-controlled markdown files in this repo. If a defense attorney wants to understand the classification logic, they read the prompt. If the department wants to update the classifier, they edit the prompt, bump the version, and the old version remains on disk forever for retroactive audit.

This is the **single most important architectural choice in the whole submission.** It's the difference between *"the AI flagged it"* and *"the AI flagged it under these specific instructions, which you can read."*

#### Layer 3 — The `reasoning` field is a required output

The schema forces Pegasus to produce a plain-English narrative explanation alongside the structured classification. From the `clip_01` NYPD compliance report:

> *"At 08:11:00, Officer White issued a clear command to 'Put the knife down' while maintaining distance, demonstrating active de-escalation. The officer continued to use calm language and maintained spatial control by closing the door behind him, preventing the subject from retreating. Despite repeated verbal commands, the subject advanced with the knife at 09:18:00, prompting the officer to discharge four rounds. The use of lethal force was initiated only after the subject re-engaged with the weapon following multiple de-escalation attempts."*

That paragraph is what an IA supervisor or defense attorney reads first. **It places the use of force in the context of the de-escalation attempts that *preceded* it.** It doesn't just say "lethal_force used" — it tells the story of how the encounter got there. Every claim is anchored to a timestamp; every quote is short and specific.

#### What we explicitly DO NOT do

- **We do not auto-file anything.** BWC-IQ produces findings; humans make decisions. Every Urgent flag goes into a queue for human review, not into a disciplinary system.
- **We do not store model outputs as "facts."** Every report is labeled as AI-generated at the top of the markdown render.
- **We do not train on individual officers.** Behavioral drift is detected at the *aggregate* level by the bias dashboard (Phase 2), never at the individual level. This prevents the system from becoming a per-officer surveillance tool — which is a hard line for civil-liberties oversight.

### 4c. Procurement pathway — how a government agency gets access

While data sovereignty and explainability were the two constraints I went deepest on, procurement is the practical blocker that determines whether the technology ever reaches the customer. Here's how BWC-IQ + TwelveLabs would actually get bought:

#### Fastest path: AWS Marketplace / Bedrock

TwelveLabs is available on **Amazon Bedrock** as a foundation model. For agencies with an existing AWS contract (Enterprise Discount Program, GovCloud account, or a blanket purchase agreement), this is the path of least resistance:

- **No new vendor procurement.** The agency is buying AWS compute, not a new software vendor. TwelveLabs usage shows up on the existing AWS bill.
- **FedRAMP inheritance.** Bedrock is FedRAMP High authorized. Models running on Bedrock inherit that authorization posture — the agency's ATO (Authority to Operate) team doesn't need to separately evaluate TwelveLabs.
- **CJIS compliance.** For law enforcement data, CJIS Security Policy applies. AWS GovCloud meets CJIS requirements. Bedrock models in GovCloud inherit that compliance.
- **Metered pricing.** Pay per API call, no upfront commitment. The pilot phase (1 precinct, 30 days) can run on a credit card-sized budget before any formal procurement is needed.

This is how we'd recommend a pilot starts: **spin up a Bedrock endpoint in the agency's existing AWS account, run shadow mode for 30 days, and produce comparison data before anyone writes an RFP.**

#### Mid-term: contract vehicles

For a full deployment beyond the pilot:

| Vehicle | How it applies |
|---|---|
| **NASA SEWP V** | Covers cloud, AI/ML, and software solutions. Many AWS partners are on SEWP. Fast ordering (~2 weeks). |
| **GSA IT Schedule 70 / MAS** | The standard federal IT procurement vehicle. If TwelveLabs or a partner SI is on schedule, agencies can issue a task order directly. |
| **NASPO ValuePoint / OMNIA Partners** | Cooperative purchasing for state and local agencies. Allows jurisdictions to piggyback on competitively bid contracts without running their own procurement. |
| **Sole-source justification** | For pilot/evaluation use under the micro-purchase threshold ($10K federal, varies by state). No competitive bid needed. |

#### Go-to-market: through a systems integrator

For a large metropolitan PD, the realistic go-to-market is **TwelveLabs as a component inside a systems integrator's solution.** The SI brings:

- The existing contract relationship and agency trust
- Security clearances and CJIS compliance posture
- Implementation team (integration with Axon/Motorola DEMS, training, change management)
- The ATO package (security documentation, pen test results, privacy impact assessment)

Likely SI partners for law enforcement video analytics: **Booz Allen Hamilton, SAIC, Deloitte, Leidos, Mark43, or Axon's professional services team** (if Axon sees this as complementary rather than competitive to their own analytics).

TwelveLabs would be positioned as the **video understanding engine** inside the SI's broader evidence management modernization proposal — not as a standalone point solution.

#### Compliance certifications that matter

| Certification | Status via Bedrock | Why it matters |
|---|---|---|
| **FedRAMP High** | Inherited from Bedrock | Required for most federal systems. Bedrock has it. |
| **CJIS** | Satisfied via GovCloud | Required for any system touching criminal justice data. |
| **StateRAMP** | Depends on deployment | For state/local agencies that don't require FedRAMP. |
| **SOC 2 Type II** | TwelveLabs SaaS path | Standard for cloud vendors. Would need to verify TwelveLabs has completed this. |
| **IL4/IL5** | GovCloud path | For DoD-adjacent use cases (military law enforcement). |

---

## 5. Scale analysis — 10K+ videos/month

**Volume:** 10,000 clips/month ≈ 14 clips/hour continuously, or ~40 clips/hour during business hours.

**Per-clip work:**

- 1 upload (`assets.create`)
- N polling calls (`assets.retrieve`) — once every 5s until `status="ready"`
- 1 triage analyze call
- 1 compliance analyze call
- 1 SHA-256 hash + 2 file writes (local, free)

**Measured per-step latency** (clip_04, 2:21 clip, 18.6 MB):

| Step | Time | Notes |
|---|---|---|
| Upload (`assets.create`) | 34.2s | Network-bound. Would be faster on agency LAN / direct AWS peering. |
| Indexing (poll until ready) | 0.1s | Short clips index near-instantly. Longer clips (12+ min) take 5-15s. |
| Triage analyze | 7.9s | Pegasus processing — scales with clip length. |
| Compliance analyze | 7.3s | Same. |
| **Total** | **49.4s** | |

At 14 clips/hour (10K/month continuous), a **single sequential worker handles the load with 95%+ idle time.** Production should still parallelize for burst tolerance and upload overlap.

**Throughput at scale (10K clips/month):**

| Metric | Value |
|---|---|
| Analyze calls/month | 20,000 (2 per clip: triage + compliance) |
| Calls/day (business hours) | ~670/day → ~28/hour |
| Rate limit ceiling | 60 req/min → 3,600/hour |
| **Headroom** | **~130x under the rate limit ceiling** |
| Sequential processing time | ~139 hours/month (all 10K clips × 50s each) |
| With 4 parallel workers | ~35 hours/month → ~1.2 hours/day |

The bottleneck at scale is **upload bandwidth**, not API rate limits or Pegasus processing time. An agency with dedicated AWS peering or VPC endpoints to Bedrock would see upload times drop from 34s to single-digit seconds per clip.

### Architecture for production scale

```
DEMS (Axon, Motorola, etc.)
   │  webhook on new clip upload
   ▼
┌──────────────────┐
│  BWC-IQ ingest   │  enqueues a job per clip
│  webhook handler │
└────────┬─────────┘
         │
         ▼
   ┌─────────────┐
   │  job queue  │  SQS / Cloud Tasks / equivalent
   └──────┬──────┘
          │
          ▼ (N parallel workers)
┌───────────────────────┐
│  BWC-IQ worker       │  client.analyze_async_task() instead of sync analyze
│  (one per shard)     │  webhook on completion → continue
└────────┬──────────────┘
         │
         ▼
┌──────────────────┐
│  Report builder  │  same logic as src/report.py
└────────┬─────────┘
         ▼
   DEMS (write back)
```

### Failure modes and mitigations

| Failure mode | Mitigation |
|---|---|
| Analyze response truncation (`finish_reason == "length"`) | Already handled in `triage.py` and `compliance.py` — they raise on truncation rather than parse malformed JSON. Falls back to a human review queue. |
| Asset processing failure (`status == "failed"`) | Retry queue with exponential backoff. After N attempts, escalate to human review. |
| Schema validation rejection (`response_format_invalid`) | Surface the raw text and route to human review. Bump the schema version after diagnosis. |
| Rate limit exceeded (429) | Exponential backoff. The async path naturally absorbs spikes. |
| Pegasus model drift after a version bump | Golden-set regression test (Phase 2) catches drift before any production traffic moves to the new version. |
| Long clips exceeding the 2-hour Pegasus limit | Chunk + merge: split the clip into 2-hour windows with overlap, run each, deduplicate events at the boundary. Untested. |
| API key compromise | Short-lived keys, rotation on a schedule, per-environment scoping. |
| Wrong model for the job | Pegasus chosen for analyze; would not use Pegasus for cross-library search. Marengo separation enforced architecturally. |

### Phased rollout

1. **Pilot — 1 precinct, 30 days.** BWC-IQ runs in **shadow mode** behind the existing manual process. Analyst-assigned priority is the source of truth; BWC-IQ's classification is collected for comparison only. Tune prompts. No operational reliance.
2. **Supervised rollout — 3 precincts, 60 days.** Analysts trust the Urgent queue but still spot-check Standard and Archive. Golden-set evaluation runs nightly. Bias metrics start being collected.
3. **Full deployment.** BWC-IQ-assigned priority drives the queue; analysts escalate by exception. Monthly bias audit review with the agency's oversight body.

This sequencing matters because it lets the system *earn* trust before it's relied on. A skeptical analyst, oversight board, or defense attorney can point to the shadow-mode comparison data and see that BWC-IQ agreed with the human analyst N% of the time before the system was given any operational weight.

---

## What's deliberately out of scope for this submission

Honesty about scope is part of the deliverable. The brief asks for at least 2 of 5 capabilities and at least 2 of 5 constraints; I went deeper on those and explicitly left others for later.

- **FOIA / PII redaction** (capability #5 from the brief) — Phase 2.
- **Cross-library Marengo search** (capability #4) — implemented. `src/search.py` + `bwc-marengo` index. Demonstrated with 7 query types across 5 clips.
- **Standalone incident summarization** (capability #3) — partially covered by the `reasoning` fields in both outputs; a dedicated summarizer is Phase 2.
- **Human-in-the-loop review UI.** Scope decision: there's no UI requirement in the brief, and a Python-script submission shows the API fluency more directly. A real deployment would not skip this.
- **Civil liberties / bias dashboard.** Acknowledged as critical (see § 3 production list) but not built — would require real demographic data and a careful evaluation methodology that exceeds the scope of a take-home.
- **Procurement pathway.** Covered in § 4c at a practical level (Bedrock as fast path, contract vehicles, SI go-to-market) but not a full RFP-ready writeup.

---

## Appendix A — Repo entry points

| Path | What it is |
|---|---|
| `src/run_demo.py` | End-to-end orchestrator. `python -m src.run_demo "clip_*.mp4"` runs every clip in `clips/`. |
| `src/{ingest,triage,compliance,report}.py` | The four Pegasus pipeline stages, each ~50 lines. |
| `src/search.py` | Marengo cross-library search: `setup_index()` to create + populate, `query()` to search. |
| `prompts/triage.v1.md`, `prompts/compliance.v1.md` | The classifier "rules" — human-readable, version-controlled markdown. |
| `schemas/triage.v1.json`, `schemas/compliance.v1.json` | Output JSON schemas for Pegasus structured responses. |
| `outputs/<clip>/report.{json,md}` | Generated reports for the four sample clips. The `.md` versions are intended for supervisor consumption. Re-running `python -m src.run_demo` regenerates them. |
| `CLAUDE.md` | Project decisions, design rationale, plan-of-attack checklist, demo presentation arc. |
| `scripts/download_clips.sh` | Reproducible footage pipeline (yt-dlp + ffmpeg). NYPD clip is age-gated; script header explains the cookies dance. |

## Appendix B — Versioning prompts and schemas

All prompts live under `prompts/` and all schemas under `schemas/`, named `<name>.<version>.{md,json}`. The current active versions are pinned in `src/config.py` (`TRIAGE_VERSION`, `COMPLIANCE_VERSION`).

To introduce a new version:

1. Copy `prompts/triage.v1.md` to `prompts/triage.v2.md` and edit.
2. Copy `schemas/triage.v1.json` to `schemas/triage.v2.json` and edit.
3. Bump `TRIAGE_VERSION = "v2"` in `src/config.py`.
4. Run `python -m src.run_demo` and compare outputs against v1 on the golden set (Phase 2).
5. Old versions remain on disk forever for retroactive audit.

This is the discipline that makes the explainability story (§ 4b) work. **Every report cites the version it used, and every version remains reproducible — even years later, even after the production system has moved to v9.**
