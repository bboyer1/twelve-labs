#!/usr/bin/env bash
#
# Download + transcode BWC demo clips. Reproducible footage pipeline.
#
# Requirements:
#   brew install yt-dlp ffmpeg
#
# IMPORTANT — age-gated clip:
#   clip_01 (NYPD 107th Precinct OIS) is age-restricted on YouTube. Before
#   running this script:
#     1. Open Chrome and sign into https://www.youtube.com/
#     2. Visit https://www.youtube.com/watch?v=-LsQHqp3GJ8 and click through
#        the "I understand and wish to proceed" age warning once
#     3. Fully Cmd+Q Chrome (not just close the window — the process must
#        exit so its cookie file is unlocked for yt-dlp to read)
#   When you re-run, macOS may prompt for keychain access — click "Always
#   Allow" so yt-dlp can decrypt the Chrome Safe Storage.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLIPS_DIR="$REPO_ROOT/clips"
mkdir -p "$CLIPS_DIR"
cd "$CLIPS_DIR"

YT_FORMAT='bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]'

download_and_transcode() {
  local label="$1"
  local out_name="$2"
  local url="$3"
  shift 3
  local extra_args=("$@")  # e.g. --cookies-from-browser chrome

  if [[ -f "$out_name" ]]; then
    echo "==> $out_name already exists, skipping"
    return 0
  fi

  echo "==> Downloading $label from $url"
  yt-dlp "${extra_args[@]}" -f "$YT_FORMAT" --merge-output-format mp4 \
    -o "_tmp_${label}.%(ext)s" "$url"

  echo "==> Transcoding $label → H.264 720p"
  ffmpeg -y -i "_tmp_${label}.mp4" \
    -c:v libx264 -preset veryfast -crf 23 \
    -c:a aac -b:a 128k \
    -movflags +faststart \
    "$out_name"
  rm -f "_tmp_${label}.mp4"

  echo "==> Done: $out_name"
  echo
}

download_and_transcode \
  "clip_01" \
  "clip_01_nypd_107pct_ois_20260126.mp4" \
  "https://www.youtube.com/watch?v=-LsQHqp3GJ8" \
  --cookies-from-browser chrome

download_and_transcode \
  "clip_02" \
  "clip_02_lapd_armed_suspect_restraining_order.mp4" \
  "https://www.youtube.com/watch?v=weeNU_BrrZ4"

echo "All clips ready:"
ls -lh "$CLIPS_DIR"/*.mp4
