# TwelveLabs SE Take-Home — Project Init

This directory holds Bret's submission for the **TwelveLabs Solutions Engineering take-home exercise** (Public Sector: Government Video Intelligence). This file is the project's north star — read it first on every session.

The full brief is at `SE-Technical Exercise- 2026.pdf`. The TwelveLabs API reference for this repo is at `skill.md` — always consult it before writing API code.

## The exercise in one paragraph

A large metropolitan police department ingests ~2,000 officers' worth of body-worn camera (BWC) footage daily. Current review is entirely manual. The department is under a court-mandated transparency order and is missing FOIA deadlines. We need to design and demo a TwelveLabs-powered solution that automates at least 2 of 5 operational capabilities, addresses at least 2 public sector constraints, and would scale to 10,000+ videos/month. Expected effort: ~4 hours. Submission format is flexible.

## Locked-in decisions

These were confirmed with Bret upfront. Do not drift from them without asking.

| Decision | Choice | Why |
|---|---|---|
| **Capabilities** (need 2 of 5) | **Triage & Prioritization** + **Policy Compliance Detection** | Both are Pegasus-structured-responses plays → one API, two prompt/schema pairs. Fastest path to a technically deep demo. |
| **Submission format** | **Python scripts + architecture doc** | Clean GitHub repo, no UI time-sink. Screen-recordable via terminal. |
| **Public sector constraints** (need 2 of 5) | **Data sovereignty & chain of custody** + **Explainability** | Bret's strongest angles. Both map directly to TwelveLabs features: Bedrock deployment for sovereignty, structured-JSON + timestamped evidence + versioned prompts for explainability. |
| **Prereqs** | API key ✅ • Footage ✅ (2 clips, see below) | |

### Sample footage on disk

All four clips transcoded to H.264/AAC 720p for TwelveLabs compatibility. All under the 200 MB direct-upload limit and within the 2-hour Pegasus analyze limit.

| File | Source | Duration | Pegasus triage | UoF | Notes |
|---|---|---|---|---|---|
| `clips/clip_01_nypd_107pct_ois_20260126.mp4` | NYPD 107th Precinct Officer-Involved Shooting, 2026-01-26 (incl. 911 call) | 12:48 | **Urgent** | `lethal_force` (4 rounds discharged) | Age-restricted on YT — required Chrome cookies. Pegasus correctly identified the de-escalation chain *preceding* the shot. |
| `clips/clip_02_lapd_armed_suspect_restraining_order.mp4` | LAPD Armed Suspect, Restraining Order Violation | 7:23 | **Urgent** | `physical_restraint` | Title implies a shooting; Pegasus did NOT classify lethal_force, which is **the correct call** — the actual shooting happens after the released clip ends. |
| `clips/clip_03_kalamazoo_dps_traffic_stop.mp4` | Kalamazoo DPS body cam (via MLive), traffic stop later disputed as racial profiling and debunked | 2:39 | **Standard** | `none` | Verbal disagreement about taillight + tint citation; Pegasus correctly held it at Standard despite the verbal escalation because no physical force occurred. |
| `clips/clip_04_nmsp_dwi_stop.mp4` | KRQE-released NM State Police DWI stop ("officer moved to tears") | 2:21 | **Standard** | `none` | DWI arrest without force; Pegasus identified the field sobriety test commands AND the discovery of a child in the trunk. |

**Coverage achieved:** 2 Urgent (with different UoF types: lethal vs physical_restraint), 2 Standard (with different contexts: traffic-stop disagreement vs DWI arrest with welfare incident). The demo can now show real discriminative classification across the priority spectrum.

## The shape of the solution

**One-line pitch:** *A two-stage Pegasus analyzer that ingests body-cam footage, produces a structured triage classification (Urgent/Standard/Archive) with timestamped evidence, and runs a policy compliance audit (Miranda, de-escalation, use-of-force type) — with every output anchored to video timestamps and prompt versions for chain-of-custody defensibility.*

**Pipeline:**

```
BWC video file
    ↓ [ingest.py] direct upload → asset_id → poll until ready
asset_id
    ↓ [triage.py]    Pegasus analyze + JSON schema  →  TriageReport
    ↓ [compliance.py] Pegasus analyze + JSON schema  →  ComplianceReport
    ↓ [report.py]    merge + sign + write chain-of-custody record
outputs/<asset_id>.json  +  outputs/<asset_id>.md
```

Both `triage.py` and `compliance.py` use `client.analyze()` with `response_format=ResponseFormat(type="json_schema", ...)` — this is the single most important TwelveLabs primitive for this submission. See `skill.md` § "Structured JSON analysis" for the exact pattern and the schema keyword limitations (no `enum`, no `minLength` — we work around both).

## Key architectural constraints to remember

1. **Marengo and Pegasus live in separate indexes.** You cannot mix them. For this demo we primarily use **Pegasus (analyze)** off raw asset IDs — no index required for analyze. If we add Cross-Library Search later, that's a separate Marengo index.
2. **Direct asset upload is synchronous up to 200 MB.** Most BWC clips will fit. Still poll `asset.status` until `"ready"` before calling analyze.
3. **Structured response schema is constrained.** Supported: `pattern`, `minimum`/`maximum`, `required`, `minItems` (0 or 1 only). **Not supported: `enum`, `minLength`, `maxLength`.** For an enum-like field (e.g. priority ∈ {Urgent, Standard, Archive}), enforce it via `pattern: "^(Urgent|Standard|Archive)$"` or via the prompt itself plus client-side validation.
4. **`max_tokens` caps at 4096.** Watch `finish_reason == "length"` and truncate gracefully. Don't let the policy schema grow unbounded.
5. **Pegasus video limits: 4 seconds to 2 hours, ≤ 2 GB.** Long BWC shifts will need chunking — mention in the scalability writeup, don't need to implement.

## Proposed repo layout

```
twelve-labs/
├── CLAUDE.md                       # this file
├── skill.md                        # TwelveLabs API reference
├── README.md                       # what this is + how to run
├── SE-Technical Exercise- 2026.pdf # the brief
├── requirements.txt                # twelvelabs, python-dotenv
├── .env.example                    # TWELVE_LABS_API_KEY=...
├── src/
│   ├── config.py                   # client, model names, paths
│   ├── ingest.py                   # upload + poll helpers
│   ├── triage.py                   # Pegasus triage prompt + schema
│   ├── compliance.py               # Pegasus compliance prompt + schema
│   ├── report.py                   # merge + chain-of-custody record
│   └── run_demo.py                 # end-to-end orchestrator (entry point)
├── prompts/                        # versioned prompt templates (explainability)
│   ├── triage.v1.md
│   └── compliance.v1.md
├── schemas/                        # versioned JSON schemas
│   ├── triage.v1.json
│   └── compliance.v1.json
├── samples/                        # sample outputs to ship with submission
│   └── <asset_id>.{json,md}
└── docs/
    ├── architecture.md             # REQUIRED deliverable — addresses both PS constraints
    └── diagram.png                 # arch diagram (optional but recommended)
```

Prompts and schemas are **versioned files on disk, not inline constants**. This is the entire explainability story in one design choice: every flag in every report cites `prompt_version` and `schema_version`, so an IA investigator or defense attorney can reproduce the exact call that produced the evidence.

## Demo presentation arc

For a ~14-minute live demo (they'll likely cap at 30, plenty of headroom):

1. **Frame the problem (1 min).** "Their analysts watch video in real time. The pain isn't 'we need a better player' — it's 'we need to know which footage to look at first.' Every decision in this submission flows from that framing."
2. **Live demo (5 min).** Run `python -m src.run_demo` on a clip. **Read the compliance reasoning paragraph aloud** — that's the moneyshot, the moment the audience realizes the output is supervisor-grade and not generic LLM riff. Then show the contrasting reports side by side: NYPD `lethal_force` with quoted de-escalation chain, LAPD `physical_restraint` (model didn't classify lethal because shooting happens after the released clip ends — *which is actually the right call*), routine clip `Standard` (once it exists).
3. **Architectural choices (3 min).** Versioned prompts on disk → explainability. SHA-256 of source file → chain of custody. Pegasus only, no Marengo → focused scope. Each one is a deliberate trade-off that maps to a customer requirement.
4. **Public sector constraints (3 min).** **Sovereignty:** TwelveLabs runs on Amazon Bedrock; footage stays in the agency tenant; that's the answer to the first question every government CIO asks. **Explainability:** every flag has a timestamp + a quoted source + a versioned prompt that produced it; an IA investigator or defense attorney can reproduce any finding.
5. **What's missing on purpose (1 min).** No UI, no Marengo search, no PII redaction, only 2 of 5 capabilities. Each is a scope decision. Here's what week 2 looks like.
6. **Gotchas (1 min).** Two of the v1.3 doc claims were wrong — `minimum`/`maximum` numeric constraints aren't actually supported, and the SDK constructor doesn't actually auto-read the env var. Both diagnosed, both worked around, both written up in `skill.md` § 6 so the next engineer doesn't lose an hour. *This is the rarest signal you'll send: that you noticed, fixed, and documented the rough edges.*

## Demo talking points (for the recording)

1. **Why Pegasus structured responses?** One API call returns both the classification and the evidence (timestamps, reasoning). This is the evidentiary unit.
2. **Data sovereignty story:** TwelveLabs is available on **Amazon Bedrock** — video never leaves the agency's AWS tenant. For on-prem agencies, the multipart-upload API means footage transits only over agency-approved egress. Chain of custody is preserved via asset_id hashes + a signed JSON record per video.
3. **Explainability story:** Every field in the output has a source: the timestamp is from Pegasus's temporal grounding, the reasoning is from Pegasus's generative text, the classification rule is from a versioned prompt file on disk. An IA investigator can replay the exact prompt against the exact asset_id and get the same evidence.
4. **Scale story:** 10K videos/month = 14 videos/hour. Async Pegasus analyze + webhook completion + SQS-style queue handles this easily. Show back-of-envelope in the architecture doc.
5. **Bias / civil liberties caveat** (even though it's not our chosen PS constraint — mention it anyway): structured output includes a `reasoning` field; human supervisor is *always* in the loop before any action is taken. The system triages, it does not decide.

## Plan of attack (sequence)

1. ☑ Source BWC footage — 2 OIS clips on disk (NYPD 12:48, LAPD 7:23). **Still need 1 routine clip** — see #9.
2. ☑ Scaffold repo layout — `src/`, `prompts/`, `schemas/`, `requirements.txt`, `.env.example`, `.gitignore`
3. ☑ `ingest.py` — direct upload + status polling, verified end-to-end
4. ☑ Triage prompt + schema (v1), `triage.py` — verified on both clips, both correctly classified `Urgent`
5. ☑ Compliance prompt + schema (v1), `compliance.py` — verified on both clips, NYPD clip correctly identified `lethal_force` with timestamped de-escalation chain
6. ☑ `report.py` — chain-of-custody (SHA-256, asset_id, prompt/schema versions, UTC timestamp) + markdown render
7. ☑ `run_demo.py` — end-to-end orchestrator
8. ☑ First commit `0980e90` — 20 files, working scaffold

**Open work (in priority order):**

9. ☑ **Routine clips added** — clip_03 (Kalamazoo traffic stop) and clip_04 (NM DWI stop) both classified `Standard` with `use_of_force=none`. Discriminative gap closed.
10. ☑ `docs/architecture.md` — full submission doc, ~4,500 words / 370 lines, covering: TL;DR, customer problem framing, solution shape with ASCII pipeline diagram, the clip_04 wow moment as a worked example, the 4 required submission questions, the 2 PS constraints in depth (data sovereignty + explainability), 10K-clip scale analysis with failure modes + phased rollout, scope honesty about what's deliberately out, and two appendices (entry points + prompt versioning discipline). Quotes the lethal_force compliance reasoning from clip_01 and the child-in-trunk reasoning from clip_04 inline as worked evidence.
11. ☐ **Prompt v2 iteration — known quirk:** Pegasus returns timestamps as `MM:SS:FF`-style strings (e.g. `09:18:00` for 9 min 18 sec into the clip), not `HH:MM:SS` as the v1 prompt requests. The schema regex `\d{2}:\d{2}:\d{2}` happily accepts both formats so reports parse fine, but the semantics are off and a careful reader will notice. v2 prompt should be explicit: "Use `MM:SS` for clips under one hour."
12. ☐ Record 3–5 min screencap of `python -m src.run_demo` — show JSON, markdown, scroll past the SHA-256 / prompt-version anchors. Most candidates skip this; bar to clear is low.
13. ☐ Demo dry-run — practice the 6-step arc (see "Demo presentation arc" section below).

## Guardrails for future sessions

- **Don't implement more than 2 capabilities** unless Bret explicitly asks. The brief says "at least 2" — doing 2 well beats doing 4 badly.
- **Don't build a UI.** Decision was made to go Python-script-only.
- **Don't inline prompts or schemas into `.py` files.** They live in `prompts/` and `schemas/` — that's the explainability story.
- **Always check `skill.md` before writing API calls.** v1.3 has specific quirks (no enum in schemas, separate Marengo/Pegasus indexes, `asset.status` polling).
