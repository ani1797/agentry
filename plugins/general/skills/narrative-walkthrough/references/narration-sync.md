# Narration sync

The core rule of this skill: **audio placement is derived from the
video's actual rendered content, not from the recording script's logged
wall-clock timestamps.** The two will not match exactly (see the
timing-drift note in recording-guide.md) — always close the loop by
inspecting the real output.

## Why the logged manifest isn't enough

`manifest.json` (written by `markScene()` during recording) reflects
*when the browser automation issued each scene transition in wall
clock*. But Playwright's video encoder can fall behind wall clock during
heavy-DOM-mutation scenes, so the offset where a scene **actually
becomes visible in the rendered file** can be several seconds later than
logged, and the drift **compounds** across subsequent scenes. Muxing
narration directly at the logged offsets reproduces the exact
narration/visual mismatch this skill exists to prevent.

## Step 1 — detect real scene cuts in the rendered video

```bash
ffmpeg -i raw/output.webm \
  -filter:v "select='gt(scene,0.15)',metadata=print:file=scenecuts.txt" \
  -f null - -v error
grep pts_time scenecuts.txt | sed -E 's/.*pts_time:([0-9.]+).*/\1/' > cut_times.txt
```

Start around threshold `0.15`–`0.35`. Lower the threshold (down to
`~0.05`) if some real transitions don't produce a detected cut — this
commonly happens for fades **between two visually similar dark/plain
scenes** (e.g. two near-black terminal props back to back), where the
overall pixel delta through the fade overlay is small even though the
content genuinely changed.

## Step 2 — cluster cuts and map onto the scene order

Detected cuts arrive as multiple close timestamps per real transition
(the fade-out spike and the fade-in spike, plus incidental hover/motion
spikes inside a scene). Cluster by gap (e.g. group points within ~1.5s
of each other; use each cluster's first timestamp), then greedily map
clusters onto the manifest's scene order — monotonically increasing,
each cluster matched to the nearest-following manifest offset within a
tolerance window (drift only grows forward, never shrinks, so search
`[manifest_offset - small_margin, manifest_offset + larger_margin]`).
See [sync_offsets.py](../scripts/sync_offsets.py) for a working
implementation of this clustering/mapping.

Scenes with **no fade boundary** (e.g. two sequential clicks within the
same page, like "approve a field" → "save") won't produce a detectable
cut at all — that's expected; interpolate their offset proportionally
from the nearest detected neighbor rather than trusting the raw manifest
value in isolation.

## Step 3 — hand-verify any transition detection missed

For any manifest scene where no cluster was found nearby (common for
dark-on-dark or visually-subtle transitions), binary-search real frames
directly:

```bash
ffmpeg -y -v error -i raw/output.webm -ss <t> -frames:v 1 probe_<t>.jpg
```

(`-ss` **after** `-i` gives an accurate, not keyframe-snapped, frame —
critical for this kind of verification.) View a few candidate
timestamps and find where the new scene's distinctive content first
appears; use that as the real offset for that scene.

## Step 4 — build the narration audio track at the real offsets

```bash
ffmpeg -y \
  -i audio/00-intro.wav -i audio/01-....wav ... \
  -filter_complex "\
    [0:a]adelay=<off0_ms>|<off0_ms>[a0]; \
    [1:a]adelay=<off1_ms>|<off1_ms>[a1]; \
    ...; \
    [a0][a1]...amix=inputs=<N>:duration=longest:dropout_transition=0,volume=<N>[aout]" \
  -map "[aout]" -ar 44100 -ac 2 narration_track.wav
```

`volume=<N>` (N = number of inputs) compensates for `amix` dividing the
level by input count — since clips don't usually overlap, this restores
each clip to its original loudness. See
[build_audio_track.sh](../scripts/build_audio_track.sh) for a script
that generates this filter graph from an offsets JSON automatically.

## Step 5 — mux the final video

```bash
ffmpeg -y -i raw/output.webm -i narration_track.wav \
  -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  final_walkthrough.mp4
```

**Do not add `-shortest`** unless you specifically want the output
truncated to the audio track's length — the audio track is typically a
few seconds shorter than the full video (trailing silence after the
last narration clip ends), and `-shortest` will clip the video's own
outro/fade-out. Let the video's full duration win.

## Step 6 — verify

- `ffprobe` the final file: confirm duration equals the raw video's
  duration (not the (shorter) audio's).
- Extract frames at each scene's **corrected** real offset (not the
  original manifest offset) and visually confirm the on-screen content
  matches that segment's narration text.
- Spot-check the scene(s) that needed hand-correction in step 3 most
  carefully — they're the ones most likely to still be off.
