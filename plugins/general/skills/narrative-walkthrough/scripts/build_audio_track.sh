#!/usr/bin/env bash
# Build a single narration audio track from per-segment TTS clips placed
# at their corrected real offsets, then mux with the recorded video.
#
# Usage:
#   build_audio_track.sh <real_offsets.json> <audio_dir> <out_track.wav>
#   mux_final.sh <video.webm> <out_track.wav> <final.mp4>   (see bottom)
#
# real_offsets.json: {"00-intro": 0.04, "01-example": 12.3, ...}
# audio_dir: contains "<id>.wav" for every key in real_offsets.json
set -euo pipefail

OFFSETS_JSON="${1:?path to real_offsets.json}"
AUDIO_DIR="${2:?directory containing <id>.wav clips}"
OUT_TRACK="${3:?output wav path}"

mapfile -t IDS < <(python3 -c "
import json,sys
d = json.load(open('$OFFSETS_JSON'))
for k in d: print(k)
")

inputs=()
filters=()
labels=()
i=0
for id in "${IDS[@]}"; do
  offset_ms=$(python3 -c "
import json
d = json.load(open('$OFFSETS_JSON'))
print(int(round(d['$id']*1000)))
")
  inputs+=(-i "$AUDIO_DIR/$id.wav")
  filters+=("[$i:a]adelay=${offset_ms}|${offset_ms}[a$i]")
  labels+=("[a$i]")
  i=$((i+1))
done

filter_complex="$(IFS=';'; echo "${filters[*]}")"
mix="$(IFS=''; echo "${labels[*]}")amix=inputs=${#IDS[@]}:duration=longest:dropout_transition=0,volume=${#IDS[@]}[aout]"

ffmpeg -y -v error "${inputs[@]}" \
  -filter_complex "${filter_complex};${mix}" \
  -map "[aout]" -ar 44100 -ac 2 "$OUT_TRACK"

echo "Wrote $OUT_TRACK"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT_TRACK"

# --- Final mux (run separately once you're happy with the audio track) ---
# ffmpeg -y -i <video.webm> -i "$OUT_TRACK" \
#   -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
#   -c:a aac -b:a 192k \
#   -movflags +faststart \
#   final_walkthrough.mp4
# NOTE: do NOT add -shortest here -- it truncates to the (usually
# shorter) audio track and clips the video's outro. Let the full video
# duration win.
