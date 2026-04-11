# BWC-IQ — Architecture

> Submission doc for the TwelveLabs SE take-home. Addresses the four required submission questions and the two chosen public sector constraints (data sovereignty & chain of custody; explainability).

**Status:** Draft — flesh out after first successful end-to-end run so the write-up can cite real outputs.

---

## 1. What TwelveLabs capabilities did you use, and why?

_TODO — flesh out after first run._

**Core primitive:** Pegasus 1.2 via `client.analyze()` with `response_format=ResponseFormat(type="json_schema", ...)`. One API endpoint, two different prompt/schema pairs produce two different structured outputs — triage and compliance. No indexes, no embeddings, no search.

**Why this and not Marengo / search?**

- The department's core pain is *per-clip* analysis (classify, summarize, audit), not *cross-library* retrieval. Pegasus is the right tool for per-clip work; Marengo is the right tool for cross-library work. We'd add Marengo as a second phase.
- Pegasus's structured-response mode lets us get both the classification *and* the evidence (timestamps, reasoning) in a single call. That's the unit of work that maps cleanly to an evidentiary record.
- One model per use case means we can version the prompt + schema and reason about outputs in isolation. Adding Marengo in parallel would double the ops surface for marginal product value at this stage.

**Key API quirks we had to work around** (see `skill.md` §6):

- No `enum` in JSON schema — we use `pattern: "^(A|B|C)$"` for enum-like fields.
- No `minLength`/`maxLength`.
- `minItems` only accepts 0 or 1.
- `max_tokens` caps at 4096. We cap triage at 2048 and compliance at 3072 with explicit `finish_reason == "length"` handling to detect truncation.
- Marengo and Pegasus cannot coexist in one index.

---

## 2. How would a government agency operationalize this? Who, when, how?

_TODO — flesh out._

### Who

| Role | Use the system for |
|---|---|
| **Triage analyst** (first shift) | Scans the Urgent queue first, assigns supervisors to each flagged clip |
| **Patrol supervisor** | Reviews every clip in their squad's Urgent queue within 24 hours (court-mandated) |
| **Internal affairs investigator** | Opens the compliance audit view on any clip under IA review |
| **FOIA / public records officer** | Uses the PII/redaction extension (future work) to prep clips for disclosure |
| **Early intervention program coordinator** | Aggregates compliance findings across officer-months to surface behavioral patterns |

### When

- **On upload** — triage runs automatically. Analyst queue is populated in priority order.
- **On incident report open** — compliance audit is surfaced alongside the officer's narrative.
- **On FOIA request** — redaction pass runs against every clip in the request scope.

### How (integration)

Connect via webhooks and a thin adapter layer to whatever **Digital Evidence Management System (DEMS)** the agency already uses:

- **Axon Evidence** — OAuth2 API, supports webhook notifications on new evidence uploads.
- **Motorola PremierOne / CommandCentral** — REST API with similar hooks.
- **Veritone Redact / Truleo** — if the agency already has a redaction vendor, we hand them the PII-flagged segments.
- **CAD** (Computer-Aided Dispatch) — pull incident metadata (call type, dispatched officers, location) as additional triage signal.

The BWC-IQ service itself is intentionally thin: it ingests a clip reference, produces a structured report, and hands it back to the DEMS. It is **not** a system of record.

---

## 3. What would you do differently with more time or in production?

_TODO — flesh out._

### Immediate (next 10 hours of work)

- **Async analyze + webhooks** instead of sync polling. `client.analyze_async_task` + webhook on completion is the right pattern for bulk ingest.
- **Multipart uploads** for full-shift BWC recordings (> 200 MB).
- **Golden-set evaluation.** A handful of clips with known-good labels, automated diff against new prompt versions. This is what makes prompt iteration defensible instead of vibes-based.
- **Confidence thresholds and fallback to human review.** Any Urgent flag under 0.8 confidence goes into a "review required" queue, not the primary Urgent queue.

### Production

- **Human-in-the-loop review UI.** React + a video player + a sidebar showing the triage JSON with clickable timestamps. 1-day build, enormous demo value.
- **Bias audit dashboard.** Track Urgent-rate by officer demographic, shift, district, and time-of-day. If any cohort drifts, trigger a prompt review.
- **Cross-library search** (Marengo) as a second phase: "show me all clips where an officer drew a firearm during a vehicle stop in the last 30 days." Separate index, separate pipeline.
- **PII / FOIA redaction** (capability #5) — detect faces, license plates, minors, medical scenes. Hand the flagged segments to a redaction vendor.
- **Fine-tuned Pegasus** on department-specific language (de-escalation protocols, policy codes). This is the biggest accuracy unlock and the most defensible.

---

## 4. Public sector constraints addressed

### 4a. Data sovereignty & chain of custody

_TODO — flesh out._

**The question a government CIO will ask first:** "Does any footage leave our environment?"

**Our answer:** TwelveLabs is available on **Amazon Bedrock**, where the model runs inside the customer's AWS account. Footage never leaves the agency's tenant. For agencies with strict data-residency requirements (state-level BWC laws, CJIS), this is the only viable deployment path — and it's a first-party TwelveLabs offering, not a bolt-on.

For agencies on the managed SaaS path, we'd recommend:
- TLS in transit (the SDK defaults to this).
- Short-lived API keys scoped per environment.
- A data-processing addendum that covers retention and subprocessor disclosure.
- A documented deletion pathway — `client.assets.delete()` removes the asset; we'd wire that into the DEMS retention schedule.

**Chain of custody** is the second half of this constraint, and it's baked into every BWC-IQ report:

- **SHA-256 of the source file** — written into `report.json` on every run. If the file is tampered with, the hash won't match.
- **TwelveLabs asset ID** — the model-side identity of the clip, linked to the source hash.
- **Prompt and schema versions** — every finding cites the exact `prompts/<name>.<ver>.md` and `schemas/<name>.<ver>.json` files used to produce it.
- **UTC generation timestamp** — ISO 8601, recorded at report-build time.
- **Model identity** — `pegasus1.2` recorded in every report.

The practical test: give an IA investigator or defense attorney the report and the original file. They can re-run the exact prompt against the exact asset, verify the hash, and reproduce the evidence. That's chain of custody.

### 4b. Explainability

_TODO — flesh out._

**The question a defense attorney will ask first:** "Why did this system classify my client's encounter as Urgent?"

**Our answer has three layers:**

1. **Every flag is anchored to a timestamp.** Pegasus's temporal grounding means the report doesn't just say "use-of-force detected" — it says "use-of-force detected at 00:03:17, confidence 0.87, type `physical_restraint`." A human can scrub to that frame and see what the model saw.

2. **Every call cites a versioned prompt and schema.** The system's "rules" are not hidden in model weights; they're in `prompts/triage.v1.md` — human-readable, version-controlled text. If a defense attorney wants to understand the classification logic, they read the prompt. If the department wants to update the classifier, they edit the prompt, bump the version, and the old version remains on disk for retroactive audit.

3. **The `reasoning` field is a required output.** The schema forces Pegasus to produce a plain-English explanation alongside the structured classification. That explanation is the narrative a supervisor or attorney reads first.

**What we explicitly do NOT do:**

- We do not auto-file reports. BWC-IQ produces findings; humans make decisions.
- We do not fine-tune on individual officers. Behavioral drift is detected at the aggregate level by the bias dashboard (future work), not at the individual level.
- We do not store model outputs as "facts." Every report is labeled as AI-generated at the top of the markdown render.

---

## 5. Scale analysis — 10K+ videos/month

_TODO — math goes here after first run._

Back-of-envelope, before measurement:

- **10K clips/month** ≈ 14 clips/hour continuously, or 40 clips/hour during business hours.
- **Sync analyze latency per clip** — measure in the first run. Expect 30–120 seconds for a 5–10 minute clip.
- **Throughput ceiling** — Pegasus analyze rate limits TBD from plan tier. Budget 2× headroom and use async tasks + queue when near the ceiling.
- **Bulk ingest path** — webhook-driven. DEMS posts a "new clip" event to BWC-IQ; BWC-IQ enqueues an async analyze task; on completion, BWC-IQ writes the report back to DEMS via DEMS API.
- **Storage cost** — reports are tiny (KB per clip); no storage concern on our side. The video is already stored in the DEMS.
- **Failure modes** — (a) analyze truncation due to long clips or complex schemas, handled via explicit `finish_reason` check; (b) asset processing failures, handled via retry queue; (c) schema validation failures, handled by surfacing the raw text and flagging for human review; (d) rate limits, handled by exponential backoff on 429s.

### Phased rollout

1. **Pilot (1 precinct, 30 days)** — run in shadow mode behind the existing manual process. Compare BWC-IQ triage against analyst-assigned priority. Tune prompts.
2. **Supervised rollout (3 precincts, 60 days)** — analysts trust the Urgent queue but still spot-check Standard/Archive. Golden-set evaluation runs nightly.
3. **Full deployment** — BWC-IQ-assigned priority drives the queue; analysts escalate by exception. Monthly bias audit review with oversight body.

---

## Appendix A — Versioned prompts and schemas

All prompts live under `prompts/` and all schemas under `schemas/`, named `<name>.<version>.{md,json}`. The current active versions are pinned in `src/config.py` (`TRIAGE_VERSION`, `COMPLIANCE_VERSION`).

To introduce a new version:
1. Copy `prompts/triage.v1.md` to `prompts/triage.v2.md` and edit.
2. Copy `schemas/triage.v1.json` to `schemas/triage.v2.json` and edit.
3. Bump `TRIAGE_VERSION = "v2"` in `src/config.py`.
4. Run `python -m src.run_demo` and compare outputs against v1 on the golden set.
5. Old versions remain on disk forever for retroactive audit.

---

## Appendix B — Out of scope for this demo

- FOIA / PII redaction (capability #5) — deliberately deferred.
- Cross-library search (capability #4) — deliberately deferred; would require a Marengo index and is a Phase 2 effort.
- Incident summarization (capability #3) — partially covered by the `reasoning` fields in both outputs; a dedicated summarizer is Phase 2.
- The human-in-the-loop review UI — scope decision: there's no UI requirement in the brief, and a Python-script submission shows the API fluency more directly.
