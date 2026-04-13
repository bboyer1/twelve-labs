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


def render_html(report: dict) -> str:
    """Browser-ready HTML report for demo recordings and supervisor review."""
    t = report["triage"]
    c = report["compliance"]
    src = report["source"]
    tl = report["twelvelabs"]

    priority = t.get("priority", "UNKNOWN")
    p_color = {"Urgent": "#dc2626", "Standard": "#ca8a04", "Archive": "#6b7280"}.get(
        priority, "#374151"
    )
    uof = c.get("use_of_force", {})
    uof_type = uof.get("type", "?")
    uof_color = {
        "lethal_force": "#dc2626", "less_lethal": "#ea580c",
        "physical_restraint": "#ca8a04", "verbal_command": "#ca8a04",
        "none": "#16a34a",
    }.get(uof_type, "#374151")

    # Build events rows
    events_html = ""
    for e in t.get("events", []):
        conf = e.get("confidence", 0)
        conf_width = int(conf * 100)
        events_html += f"""
        <tr>
          <td><code>{e.get("timestamp", "?")}</code></td>
          <td>{e.get("type", "?")}</td>
          <td>
            <div class="conf-bar"><div class="conf-fill" style="width:{conf_width}%"></div></div>
            <span class="conf-label">{conf:.0%}</span>
          </td>
        </tr>"""

    # Build de-escalation rows
    deesc_html = ""
    for d in c.get("deescalation", []):
        quote = d.get("quote", "")
        quote_cell = f'<span class="quote">"{quote}"</span>' if quote else ""
        deesc_html += f"""
        <tr>
          <td><code>{d.get("timestamp", "?")}</code></td>
          <td>{d.get("technique", "?")}</td>
          <td>{quote_cell}</td>
        </tr>"""

    miranda = c.get("miranda", {})
    miranda_badge = (
        '<span class="badge badge-green">Delivered</span>'
        if miranda.get("delivered")
        else '<span class="badge badge-gray">Not Delivered</span>'
    )
    miranda_detail = ""
    if miranda.get("delivered") and miranda.get("timestamp"):
        miranda_detail = f' at <code>{miranda["timestamp"]}</code>'
    if miranda.get("quote"):
        miranda_detail += f' — <span class="quote">"{miranda["quote"]}"</span>'

    uof_detail = ""
    if uof.get("timestamp") and uof.get("timestamp").strip(":"):
        uof_detail += f' at <code>{uof["timestamp"]}</code>'
    if uof.get("description"):
        uof_detail += f"<br>{uof['description']}"

    positioning = c.get("positioning", {})

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BWC Report — {src["file"]}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f8fafc; color: #1e293b; line-height: 1.6; padding: 2rem; max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
  h2 {{ font-size: 1.15rem; color: #334155; margin: 2rem 0 0.75rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.3rem; }}
  .meta {{ color: #64748b; font-size: 0.85rem; margin-bottom: 1.5rem; }}
  .meta code {{ background: #f1f5f9; padding: 0.1rem 0.35rem; border-radius: 3px; font-size: 0.8rem; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.7rem; border-radius: 9999px; font-weight: 600;
            font-size: 0.85rem; color: white; }}
  .badge-priority {{ background: {p_color}; font-size: 1.1rem; padding: 0.3rem 1rem; }}
  .badge-green {{ background: #16a34a; }}
  .badge-gray {{ background: #6b7280; }}
  .badge-uof {{ background: {uof_color}; }}
  .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem; margin: 0.75rem 0; }}
  .reasoning {{ background: #fffbeb; border-left: 4px solid #f59e0b; padding: 1rem 1.25rem; border-radius: 0 6px 6px 0;
                margin: 0.75rem 0; font-style: italic; color: #92400e; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ text-align: left; padding: 0.5rem 0.75rem; background: #f1f5f9; color: #475569; font-weight: 600; }}
  td {{ padding: 0.5rem 0.75rem; border-top: 1px solid #e2e8f0; }}
  code {{ background: #f1f5f9; padding: 0.1rem 0.35rem; border-radius: 3px; font-size: 0.85rem; }}
  .quote {{ color: #6b7280; font-style: italic; }}
  .conf-bar {{ display: inline-block; width: 60px; height: 8px; background: #e2e8f0; border-radius: 4px; vertical-align: middle; }}
  .conf-fill {{ height: 100%; background: #3b82f6; border-radius: 4px; }}
  .conf-label {{ font-size: 0.8rem; color: #64748b; margin-left: 0.3rem; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
  .grid .card {{ margin: 0; }}
  .label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 0.25rem; }}
  .value {{ font-size: 1rem; font-weight: 500; }}
  .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 0.75rem; }}
  .ai-notice {{ background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 0.5rem 0.75rem;
                font-size: 0.8rem; color: #92400e; margin-bottom: 1.5rem; }}
</style>
</head>
<body>

<div class="ai-notice">This report was generated by AI (Pegasus 1.2) and is intended for human review, not as a final determination.</div>

<h1>BWC Report</h1>
<div class="meta">
  {src["file"]}<br>
  Generated {report["generated_at"][:19]}Z &nbsp;|&nbsp;
  Asset <code>{tl["asset_id"]}</code> &nbsp;|&nbsp;
  Prompt <code>triage.{t.get("_prompt_version", "?")}</code> + <code>compliance.{c.get("_prompt_version", "?")}</code>
</div>

<h2>Triage Classification</h2>
<div class="card">
  <span class="badge badge-priority">{priority}</span>
  <p style="margin-top: 0.75rem;">{t.get("reasoning", "")}</p>
</div>

<table>
  <thead><tr><th>Timestamp</th><th>Event</th><th>Confidence</th></tr></thead>
  <tbody>{events_html if events_html else "<tr><td colspan='3' style='color:#94a3b8'>No events flagged</td></tr>"}
  </tbody>
</table>

<h2>Policy Compliance</h2>

<div class="grid">
  <div class="card">
    <div class="label">Miranda Rights</div>
    <div class="value">{miranda_badge}{miranda_detail}</div>
  </div>
  <div class="card">
    <div class="label">Use of Force</div>
    <div class="value"><span class="badge badge-uof">{uof_type}</span>{uof_detail}</div>
  </div>
</div>

<div class="card">
  <div class="label">Officer Positioning</div>
  <div class="value">{positioning.get("assessment", "N/A")}</div>
</div>

{"<h3 style='margin-top:1.25rem; font-size:1rem; color:#334155;'>De-escalation Instances</h3>" + '''
<table>
  <thead><tr><th>Timestamp</th><th>Technique</th><th>Quote</th></tr></thead>
  <tbody>''' + deesc_html + "</tbody></table>" if deesc_html else ""}

<div class="reasoning">
  <strong>Compliance Summary</strong><br>
  {c.get("reasoning", "")}
</div>

<h2>Chain of Custody</h2>
<div class="card" style="font-size: 0.85rem;">
  <table>
    <tr><td style="width:140px; color:#64748b; border:none;">SHA-256</td><td style="border:none;"><code style="font-size:0.75rem;">{src["sha256"]}</code></td></tr>
    <tr><td style="color:#64748b; border:none;">File size</td><td style="border:none;">{src["bytes"]:,} bytes</td></tr>
    <tr><td style="color:#64748b; border:none;">Asset ID</td><td style="border:none;"><code>{tl["asset_id"]}</code></td></tr>
    <tr><td style="color:#64748b; border:none;">Model</td><td style="border:none;">{tl["model"]}</td></tr>
    <tr><td style="color:#64748b; border:none;">Triage prompt</td><td style="border:none;">triage.{t.get("_prompt_version", "?")}</td></tr>
    <tr><td style="color:#64748b; border:none;">Compliance prompt</td><td style="border:none;">compliance.{c.get("_prompt_version", "?")}</td></tr>
  </table>
</div>

<div class="footer">
  Generated by BWC-IQ &nbsp;|&nbsp; Pegasus {tl["model"]} &nbsp;|&nbsp; {report["generated_at"]}
</div>

</body>
</html>"""


def save_report(report: dict, outputs_dir: Path) -> Path:
    """Write report as .json, .md, and .html under outputs/<stem>/."""
    stem = Path(report["source"]["file"]).stem
    target_dir = outputs_dir / stem
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "report.json").write_text(json.dumps(report, indent=2))
    (target_dir / "report.md").write_text(render_markdown(report))
    (target_dir / "report.html").write_text(render_html(report))
    return target_dir
