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

Both clips transcoded to H.264/AAC 720p for TwelveLabs compatibility. Both are under the 200 MB direct-upload limit and well within the 2-hour Pegasus analyze limit.

| File | Source | Duration | Size | Notes |
|---|---|---|---|---|
| `clips/clip_01_nypd_107pct_ois_20260126.mp4` | NYPD 107th Precinct Officer-Involved Shooting, 2026-01-26 (incl. 911 call) | 12:48 | 64 MB | Age-restricted on YT — required Chrome cookies to download |
| `clips/clip_02_lapd_armed_suspect_restraining_order.mp4` | LAPD Armed Suspect, Restraining Order Violation | 7:23 | 91 MB | Officer-involved shooting |

**⚠️ Discriminative-classification risk:** Both clips are officer-involved shootings and will almost certainly classify as **Urgent** triage. That's fine for "the classifier works" but weak for demonstrating *discrimination* between priority levels. Before recording the demo, consider adding a third "routine" clip (traffic stop, welfare check, routine patrol) so the triage output shows at least one Standard/Archive classification to contrast against. Policy-compliance detection will still show variance across both clips (Miranda delivery, de-escalation language, UoF type) so that dimension is fine as-is.

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

## Demo talking points (for the recording)

1. **Why Pegasus structured responses?** One API call returns both the classification and the evidence (timestamps, reasoning). This is the evidentiary unit.
2. **Data sovereignty story:** TwelveLabs is available on **Amazon Bedrock** — video never leaves the agency's AWS tenant. For on-prem agencies, the multipart-upload API means footage transits only over agency-approved egress. Chain of custody is preserved via asset_id hashes + a signed JSON record per video.
3. **Explainability story:** Every field in the output has a source: the timestamp is from Pegasus's temporal grounding, the reasoning is from Pegasus's generative text, the classification rule is from a versioned prompt file on disk. An IA investigator can replay the exact prompt against the exact asset_id and get the same evidence.
4. **Scale story:** 10K videos/month = 14 videos/hour. Async Pegasus analyze + webhook completion + SQS-style queue handles this easily. Show back-of-envelope in the architecture doc.
5. **Bias / civil liberties caveat** (even though it's not our chosen PS constraint — mention it anyway): structured output includes a `reasoning` field; human supervisor is *always* in the loop before any action is taken. The system triages, it does not decide.

## Plan of attack (sequence)

1. ☐ Source 2-3 short BWC clips from NYPD/LAPD YouTube (mix of routine + noteworthy)
2. ☐ Scaffold repo layout, `requirements.txt`, `.env.example`, `config.py`
3. ☐ Write `ingest.py` + smoke test: upload one clip → get asset_id → poll
4. ☐ Write triage prompt + schema (v1), wire up `triage.py`, test on one clip
5. ☐ Write compliance prompt + schema (v1), wire up `compliance.py`, test on one clip
6. ☐ Write `report.py` — merge outputs, add chain-of-custody record (hash, timestamps, prompt versions)
7. ☐ Write `run_demo.py` — end-to-end orchestrator over all sample clips
8. ☐ Write `docs/architecture.md` — answer the 4 required submission questions + the 2 PS constraints
9. ☐ (Optional) Record 3-5 min screencap walking through `run_demo.py` output

## Guardrails for future sessions

- **Don't implement more than 2 capabilities** unless Bret explicitly asks. The brief says "at least 2" — doing 2 well beats doing 4 badly.
- **Don't build a UI.** Decision was made to go Python-script-only.
- **Don't inline prompts or schemas into `.py` files.** They live in `prompts/` and `schemas/` — that's the explainability story.
- **Always check `skill.md` before writing API calls.** v1.3 has specific quirks (no enum in schemas, separate Marengo/Pegasus indexes, `asset.status` polling).
