# BWC-IQ -- Body-Worn Camera Triage & Compliance

Submission for the **TwelveLabs Solutions Engineering Take-Home Exercise** -- Public Sector: Government Video Intelligence.

A TwelveLabs-powered pipeline for a metropolitan police department that ingests body-worn camera (BWC) footage and produces, per clip:

1. **Triage classification** -- `Urgent` / `Standard` / `Archive` with timestamped evidence
2. **Policy compliance audit** -- Miranda delivery, de-escalation language, use-of-force type, officer-subject positioning
3. **Cross-library search** -- natural-language queries across all indexed footage via Marengo 3.0

Every output is chain-of-custody-ready: each report embeds the source file's SHA-256, the TwelveLabs asset ID, the exact prompt and schema versions used, and a UTC generation timestamp.

## Demo Recording

[Watch the demo walkthrough](https://drive.google.com/file/d/13kJlHswl0ttXWTIEz5GzzGXUtpHWAYmU/view?usp=sharing)

## Architecture

![BWC-IQ Architecture](docs/architecture.png)

## What's used from TwelveLabs

| Model | Purpose | API |
|-------|---------|-----|
| **Pegasus 1.2** | Per-clip triage + compliance via structured JSON | `client.analyze()` with `response_format=ResponseFormat(type="json_schema", ...)` |
| **Marengo 3.0** | Cross-library natural-language search | `client.search.query()` against a Marengo index |

See [`docs/architecture.md`](./docs/architecture.md) for the full solution design, scale analysis, and public sector constraint writeup.

## Quickstart

```bash
# 1. Install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env  # then add your TWELVE_LABS_API_KEY

# 3. Get sample footage
./scripts/download_clips.sh

# 4a. Run the CLI demo
python -m src.run_demo          # lean output
python -m src.run_demo -v       # verbose with Rich formatting

# 4b. Run the Streamlit dashboard
streamlit run app.py
```

The CLI writes reports to `outputs/<clip>/report.{json,md,html}`. The Streamlit dashboard reads from the same directory and adds live Marengo search and a re-analyze comparison view.

## Repo layout

```
.
├── app.py                  # Streamlit dashboard (analyst queue, detail, search)
├── src/
│   ├── config.py           # client, paths, versions, prompt/schema loaders
│   ├── ingest.py           # direct-upload + status polling
│   ├── triage.py           # Pegasus structured analyze -- triage
│   ├── compliance.py       # Pegasus structured analyze -- policy audit
│   ├── search.py           # Marengo cross-library search
│   ├── report.py           # merge + chain-of-custody record + MD/HTML render
│   └── run_demo.py         # CLI orchestrator (uses indexes.json when available)
├── prompts/                # versioned prompt templates (explainability)
│   ├── triage.v1.md
│   └── compliance.v1.md
├── schemas/                # versioned JSON schemas
│   ├── triage.v1.json
│   └── compliance.v1.json
├── outputs/                # generated reports + indexes.json (committed)
├── docs/
│   └── architecture.md     # solution design, scale analysis, PS constraints
├── scripts/
│   └── download_clips.sh   # reproducible footage pipeline (yt-dlp + ffmpeg)
├── clips/                  # BWC footage (gitignored, reproduced via script)
├── requirements.txt
└── .env.example
```

## Design notes

- **Prompts and schemas are versioned files on disk**, never inline Python constants. Every report cites `_prompt_version` and `_schema_version` so an IA investigator or defense attorney can reproduce the exact call.
- **Pre-indexed assets.** `outputs/indexes.json` stores asset IDs and index IDs from TwelveLabs. The CLI and Streamlit app use these to skip re-upload when clips are already indexed.
- **Two indexes, not one.** Marengo and Pegasus cannot coexist in the same index. The demo creates `bwc-pegasus` and `bwc-marengo` separately.
- **JSON-schema workarounds.** The v1.3 analyze endpoint doesn't support `enum`, `minLength`, or numeric constraints. Enum-like fields use `pattern: "^(A|B|C)$"` instead. See `docs/architecture.md` for details.
