"""End-to-end demo orchestrator.

Run with:
    python -m src.run_demo                  # process every clip in clips/
    python -m src.run_demo clip_01_*.mp4    # process one clip by glob

Pipeline for each clip:
    ingest  →  triage  →  compliance  →  build_report  →  save_report
"""

from __future__ import annotations

import sys
from pathlib import Path

from .compliance import compliance
from .config import CLIPS_DIR, OUTPUTS_DIR
from .ingest import ingest
from .report import build_report, save_report
from .triage import triage


def discover_clips(clips_dir: Path, pattern: str = "clip_*.mp4") -> list[Path]:
    return sorted(clips_dir.glob(pattern))


def process_clip(clip_path: Path) -> Path:
    print(f"\n=== {clip_path.name} ===")

    print("  [1/4] uploading + waiting for ready...")
    asset_id = ingest(clip_path)
    print(f"        asset_id = {asset_id}")

    print("  [2/4] triage (Pegasus structured analyze)...")
    triage_result = triage(asset_id)
    print(f"        priority = {triage_result.get('priority', '?')}")

    print("  [3/4] compliance audit (Pegasus structured analyze)...")
    compliance_result = compliance(asset_id)

    print("  [4/4] building chain-of-custody report...")
    report = build_report(
        clip_path=clip_path,
        asset_id=asset_id,
        triage_result=triage_result,
        compliance_result=compliance_result,
    )
    out_dir = save_report(report, OUTPUTS_DIR)
    print(f"        saved → {out_dir}")
    return out_dir


def main(argv: list[str]) -> int:
    pattern = argv[0] if argv else "clip_*.mp4"
    clips = discover_clips(CLIPS_DIR, pattern=pattern)
    if not clips:
        print(
            f"No clips matching '{pattern}' found under {CLIPS_DIR}.\n"
            f"Run ./scripts/download_clips.sh first.",
            file=sys.stderr,
        )
        return 1
    print(f"Processing {len(clips)} clip(s) sequentially.")
    for clip in clips:
        try:
            process_clip(clip)
        except Exception as e:  # noqa: BLE001
            print(f"  !! FAILED: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
