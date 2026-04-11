"""Upload BWC clips to TwelveLabs and wait until they're ready for analysis.

Pattern from skill.md §4. Direct-upload path only — sufficient for the demo
since all sample clips are well under the 200 MB direct-upload limit. The
production path for full-shift BWC recordings (> 200 MB) would use the
multipart upload API; noted in docs/architecture.md.
"""

from __future__ import annotations

import time
from pathlib import Path

from .config import get_client


def upload_video(file_path: Path) -> str:
    """Direct-upload a video file and return the asset_id.

    The asset will be in 'processing' status when this returns — callers
    must call wait_for_ready() before running analyze against it.
    """
    client = get_client()
    with open(file_path, "rb") as fh:
        asset = client.assets.create(
            method="direct",
            file=fh,
            filename=file_path.name,
        )
    return asset.id


def wait_for_ready(
    asset_id: str,
    poll_interval: float = 5.0,
    max_wait_seconds: float = 900.0,
) -> None:
    """Poll asset.status until 'ready'. Raise on 'failed' or timeout.

    Sample clips process in well under 5 minutes; max_wait is generous.
    """
    client = get_client()
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        asset = client.assets.retrieve(asset_id=asset_id)
        status = asset.status
        if status == "ready":
            return
        if status == "failed":
            raise RuntimeError(f"Asset {asset_id} failed to process")
        time.sleep(poll_interval)
    raise TimeoutError(
        f"Asset {asset_id} did not reach 'ready' within {max_wait_seconds}s"
    )


def ingest(file_path: Path) -> str:
    """Upload + wait end-to-end. Returns a ready asset_id."""
    asset_id = upload_video(file_path)
    wait_for_ready(asset_id)
    return asset_id
