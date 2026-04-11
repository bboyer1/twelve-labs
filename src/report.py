"""Merge triage + compliance results into a chain-of-custody report.

Every report is a JSON object that includes:
  - source file name + SHA-256 hash (chain of custody)
  - asset_id (TwelveLabs-side identity)
  - triage result with _prompt_version / _schema_version
  - compliance result with _prompt_version / _schema_version
  - model name (pegasus1.2)
  - UTC generation timestamp

This is what makes the demo defensible: an IA investigator or defense
attorney can reproduce any flag by running the named prompt + schema
against the named asset_id.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import PEGASUS_MODEL


def chain_of_custody_hash(file_path: Path) -> str:
    """Return hex SHA-256 of the source file, streaming in 1 MiB chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_report(
    *,
    clip_path: Path,
    asset_id: str,
    triage_result: dict,
    compliance_result: dict,
) -> dict:
    return {
        "source": {
            "file": clip_path.name,
            "sha256": chain_of_custody_hash(clip_path),
            "bytes": clip_path.stat().st_size,
        },
        "twelvelabs": {
            "asset_id": asset_id,
            "model": PEGASUS_MODEL,
        },
        "triage": triage_result,
        "compliance": compliance_result,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def render_markdown(report: dict) -> str:
    """Human-readable version for supervisor review."""
    t = report["triage"]
    c = report["compliance"]
    src = report["source"]
    tl = report["twelvelabs"]

    lines = [
        f"# BWC Report — {src['file']}",
        "",
        f"- **Generated:** {report['generated_at']}",
        f"- **Asset ID:** `{tl['asset_id']}`",
        f"- **Model:** `{tl['model']}`",
        f"- **SHA-256:** `{src['sha256']}`",
        "",
        "## Triage",
        f"- **Priority:** **{t.get('priority', 'UNKNOWN')}**",
        f"- **Reasoning:** {t.get('reasoning', '')}",
        f"- **Prompt / schema version:** `{t.get('_prompt_version', '?')}` / `{t.get('_schema_version', '?')}`",
        "",
        "### Events",
    ]
    events = t.get("events", [])
    if not events:
        lines.append("_(no events flagged)_")
    else:
        for event in events:
            lines.append(
                f"- `{event.get('timestamp', '?')}` — **{event.get('type', '?')}** "
                f"(confidence {event.get('confidence', 0):.2f})"
            )

    lines += [
        "",
        "## Policy Compliance",
        f"- **Prompt / schema version:** `{c.get('_prompt_version', '?')}` / `{c.get('_schema_version', '?')}`",
        f"- **Reasoning:** {c.get('reasoning', '')}",
        "",
        "### Raw finding",
        "```json",
        json.dumps(
            {k: v for k, v in c.items() if not k.startswith("_")},
            indent=2,
        ),
        "```",
    ]
    return "\n".join(lines) + "\n"


def save_report(report: dict, outputs_dir: Path) -> Path:
    """Write report as both .json and .md under outputs/<stem>/."""
    stem = Path(report["source"]["file"]).stem
    target_dir = outputs_dir / stem
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "report.json").write_text(json.dumps(report, indent=2))
    (target_dir / "report.md").write_text(render_markdown(report))
    return target_dir
