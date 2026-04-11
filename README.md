# BWC-IQ — Body-Worn Camera Triage & Compliance

Submission for the **TwelveLabs Solutions Engineering Take-Home Exercise** — Public Sector: Government Video Intelligence.

A TwelveLabs-powered pipeline for a metropolitan police department that ingests body-worn camera (BWC) footage and produces, per clip:

1. **Triage classification** — `Urgent` / `Standard` / `Archive` with timestamped evidence
2. **Policy compliance audit** — Miranda delivery, de-escalation language, use-of-force type, officer-subject positioning

Every output is chain-of-custody-ready: each report embeds the source file's SHA-256, the TwelveLabs asset ID, the exact prompt and schema versions used, and a UTC generation timestamp.

## What's used from TwelveLabs

- **Pegasus 1.2** via `client.analyze()` with `response_format=ResponseFormat(type="json_schema", ...)` — the entire demo rides on this one primitive.
- No Marengo / indexes / search. Analyze runs directly off asset IDs without an index, which keeps the architecture simple and lets us reason about one model's behavior at a time.

See [`skill.md`](./skill.md) for the full API reference and [`docs/architecture.md`](./docs/architecture.md) for how this would scale to 10K+ videos/month in a government environment.

## Quickstart

```bash
# 1. Install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env  # then edit .env and add your TWELVE_LABS_API_KEY

# 3. Get sample footage
#    The NYPD clip is age-gated on YouTube — read the script header first.
./scripts/download_clips.sh

# 4. Run the demo
python -m src.run_demo
```

Outputs land in `outputs/<clip_stem>/` as `report.json` and `report.md`.

## Repo layout

```
.
├── CLAUDE.md               # project init — design rationale, decisions, plan
├── skill.md                # TwelveLabs v1.3 API reference
├── README.md               # this file
├── requirements.txt
├── .env.example
├── clips/                  # downloaded BWC clips (gitignored)
├── src/
│   ├── config.py           # client, paths, versions, prompt/schema loaders
│   ├── ingest.py           # direct-upload + status polling
│   ├── triage.py           # Pegasus structured analyze for triage
│   ├── compliance.py       # Pegasus structured analyze for policy audit
│   ├── report.py           # merge + chain-of-custody record + markdown render
│   └── run_demo.py         # end-to-end orchestrator (entry point)
├── prompts/                # versioned prompt templates (explainability)
│   ├── triage.v1.md
│   └── compliance.v1.md
├── schemas/                # versioned JSON schemas
│   ├── triage.v1.json
│   └── compliance.v1.json
├── scripts/
│   └── download_clips.sh   # reproducible footage pipeline (yt-dlp + ffmpeg)
├── docs/
│   └── architecture.md     # addresses the 4 submission questions + 2 PS constraints
├── samples/                # committed example outputs (populate after first run)
└── outputs/                # runtime reports (gitignored)
```

## Design notes

- **Prompts and schemas live as versioned files on disk**, never inline Python constants. This is the entire explainability story in one design choice: every field in every report cites `_prompt_version` and `_schema_version`, so an IA investigator or defense attorney can re-run the exact call that produced the evidence.
- **Direct-upload only.** Sample clips are all under 200 MB. The production path for full-shift BWC (> 200 MB) would use multipart uploads — noted in `docs/architecture.md`.
- **No index creation.** Analyze works off raw `asset_id`. If we add cross-library search, that would be a separate Marengo index — two indexes can't coexist.
- **JSON-schema workarounds.** The v1.3 analyze endpoint doesn't support `enum`, `minLength`, or `maxLength`. Enum-like fields use `pattern: "^(A|B|C)$"` instead. See `skill.md` §6.
