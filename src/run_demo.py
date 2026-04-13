"""End-to-end demo orchestrator.

Run with:
    python -m src.run_demo                      # lean output (default)
    python -m src.run_demo -v                   # verbose: spinners, colors, timing, summary table
    python -m src.run_demo -v clip_01_*.mp4     # verbose + specific clip

Verbose mode requires: pip install rich  (included in requirements.txt)
"""

from __future__ import annotations

import argparse
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from .compliance import compliance
from .config import CLIPS_DIR, COMPLIANCE_VERSION, OUTPUTS_DIR, TRIAGE_VERSION
from .ingest import ingest
from .report import build_report, save_report
from .triage import triage

# Style maps — only consumed by verbose path, but defined once.
_P_STYLE = {"Urgent": "red bold", "Standard": "yellow", "Archive": "dim"}
_U_STYLE = {
    "lethal_force": "red bold",
    "less_lethal": "red",
    "physical_restraint": "yellow",
    "verbal_command": "yellow",
    "none": "green",
}


def discover_clips(clips_dir: Path, pattern: str = "clip_*.mp4") -> list[Path]:
    return sorted(clips_dir.glob(pattern))


@contextmanager
def _step(label: str, console):
    """Wrap a pipeline step with a spinner (verbose) or a plain print."""
    t0 = time.time()
    if console:
        with console.status(f"[bold blue]  {label}...[/]", spinner="dots"):
            yield lambda: time.time() - t0
    else:
        print(f"  {label}...")
        yield lambda: time.time() - t0


def process_clip(clip_path: Path, console=None) -> dict:
    """Run the full pipeline on one clip. Returns a result dict."""
    name = clip_path.name
    v = console is not None  # verbose?
    t_start = time.time()

    if v:
        console.print()
        console.rule(f"[bold]{name}[/]")
        console.print()
    else:
        print(f"\n=== {name} ===")

    # 1. Upload + index
    with _step("Uploading + indexing", console) as elapsed:
        asset_id = ingest(clip_path)
    if v:
        console.print(
            f"  [green]✓[/] Ready — asset_id=[dim]{asset_id[:12]}...[/] [dim]({elapsed():.1f}s)[/]"
        )
    else:
        print(f"        asset_id = {asset_id}")

    # 2. Triage
    with _step(f"Triage (triage.{TRIAGE_VERSION})", console) as elapsed:
        triage_result = triage(asset_id)
    priority = triage_result.get("priority", "?")
    events = triage_result.get("events", [])
    if v:
        console.print(
            f"  [green]✓[/] Priority: [{_P_STYLE.get(priority, 'white')}]{priority}[/]"
            f" — {len(events)} events [dim]({elapsed():.1f}s)[/]"
        )
        top = sorted(events, key=lambda e: e.get("confidence", 0), reverse=True)[:3]
        if top:
            parts = [
                f"[bold]{e.get('type', '?')}[/] @ {e.get('timestamp', '?')}"
                for e in top
            ]
            console.print(f"    └─ {' · '.join(parts)}")
    else:
        print(f"        priority = {priority}")

    # 3. Compliance
    with _step(f"Compliance (compliance.{COMPLIANCE_VERSION})", console) as elapsed:
        compliance_result = compliance(asset_id)
    uof = compliance_result.get("use_of_force", {})
    uof_type = uof.get("type", "?")
    if v:
        miranda = compliance_result.get("miranda", {})
        deesc = compliance_result.get("deescalation", [])
        reasoning = compliance_result.get("reasoning", "")
        console.print(f"  [green]✓[/] Compliance complete [dim]({elapsed():.1f}s)[/]")
        m = (
            "[green]delivered[/]"
            if miranda.get("delivered")
            else "[dim]not delivered[/]"
        )
        console.print(f"    ├─ Miranda: {m}")
        console.print(f"    ├─ De-escalation: {len(deesc)} instance(s)")
        u_style = _U_STYLE.get(uof_type, "white")
        u_label = f"[{u_style}]{uof_type}[/]"
        uof_ts = uof.get("timestamp", "")
        if uof_ts and uof_ts.strip(":"):
            u_label += f" @ {uof_ts}"
        console.print(f"    ├─ Use of force: {u_label}")
        preview = reasoning[:140].rstrip() + ("..." if len(reasoning) > 140 else "")
        console.print(f'    └─ [italic dim]"{preview}"[/]')
    else:
        print(f"        use_of_force = {uof_type}")

    # 4. Report (same in both modes)
    report = build_report(
        clip_path=clip_path,
        asset_id=asset_id,
        triage_result=triage_result,
        compliance_result=compliance_result,
    )
    out_dir = save_report(report, OUTPUTS_DIR)
    total = time.time() - t_start
    if v:
        console.print(
            f"  [green]✓[/] Report → {out_dir.name}/ [dim]({total:.1f}s total)[/]"
        )
    else:
        print(f"        saved → {out_dir}")

    return {
        "name": clip_path.stem,
        "priority": priority,
        "uof_type": uof_type,
        "event_count": len(events),
        "total_seconds": total,
    }


def _print_summary(results: list[dict], console) -> None:
    """Rich summary table — only called in verbose mode."""
    from rich.table import Table

    table = Table(title="[bold]Summary[/]", border_style="blue", show_lines=True)
    table.add_column("Clip", style="bold", max_width=48)
    table.add_column("Priority", justify="center")
    table.add_column("Use of Force", justify="center")
    table.add_column("Events", justify="center")
    table.add_column("Time", justify="right", style="dim")

    total_time = 0.0
    for r in results:
        if "error" in r:
            table.add_row(r["name"], "[red]ERROR[/]", r.get("error", ""), "", "")
            continue
        table.add_row(
            r["name"],
            f"[{_P_STYLE.get(r['priority'], 'white')}]{r['priority']}[/]",
            f"[{_U_STYLE.get(r['uof_type'], 'white')}]{r['uof_type']}[/]",
            str(r["event_count"]),
            f"{r['total_seconds']:.1f}s",
        )
        total_time += r["total_seconds"]

    console.print()
    console.print(table)
    console.print(
        f"\n  [bold]{len(results)}[/] clip(s) in [bold]{total_time:.1f}s[/] total\n"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="BWC-IQ demo orchestrator")
    parser.add_argument(
        "pattern",
        nargs="?",
        default="clip_*.mp4",
        help="glob pattern for clips (default: clip_*.mp4)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="rich output with spinners, colors, and summary table",
    )
    args = parser.parse_args(argv)

    # Lazy-import rich only when requested
    console = None
    if args.verbose:
        try:
            from rich.console import Console
            from rich.panel import Panel

            console = Console()
        except ImportError:
            print("rich not installed. Run: pip install rich", file=sys.stderr)
            print("Falling back to default output.\n", file=sys.stderr)

    clips = discover_clips(CLIPS_DIR, pattern=args.pattern)
    if not clips:
        msg = (
            f"No clips matching '{args.pattern}' found under {CLIPS_DIR}.\n"
            f"Run ./scripts/download_clips.sh first."
        )
        print(msg, file=sys.stderr) if not console else console.print(f"[red]{msg}[/]")
        return 1

    if console:
        console.print()
        console.print(
            Panel(
                f"Processing [bold]{len(clips)}[/] clip(s) sequentially\n"
                f"Prompts: [cyan]triage.{TRIAGE_VERSION}[/] + [cyan]compliance.{COMPLIANCE_VERSION}[/]",
                title="[bold]BWC-IQ Demo[/]",
                border_style="blue",
            )
        )
    else:
        print(f"Processing {len(clips)} clip(s) sequentially.")

    results: list[dict] = []
    for clip in clips:
        try:
            results.append(process_clip(clip, console=console))
        except Exception as e:  # noqa: BLE001
            err = f"FAILED: {e}"
            print(f"  !! {err}", file=sys.stderr) if not console else console.print(
                f"  [red bold]✗ {err}[/]"
            )
            results.append({"name": clip.stem, "error": str(e)})

    if console:
        _print_summary(results, console)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
