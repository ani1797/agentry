---
name: narrative-walkthrough
description: >
  Build automated, narrated screen-by-screen walkthrough videos of any live
  web app (or other Playwright-drivable UI) by combining a single
  continuous headless-browser recording of real actions with
  TTS narration synced to real detected on-screen transitions.
  USE FOR: demo/onboarding videos, feature walkthroughs, release recap
  videos, "show it don't say it" product tours, re-generating a stale or
  jarring manually-recorded demo video for any project.
  DO NOT USE FOR: static slide decks (use marp-slides), single screenshots,
  hand-animated marketing motion graphics, diagrams (use mermaid).
allowed-tools: write(/tmp/narrative-walkthrough/**)
compatibility:
  cli: node, ffmpeg, ffprobe — see references/getting-started.md
  npm: playwright (or @playwright/test) installed somewhere in the target
    repo; a system Chrome/Chromium binary if the bundled one isn't
    downloaded
  tts: any local or cloud text-to-speech engine reachable over HTTP or CLI
    (e.g. a local Kokoro-FastAPI Docker container, `say`, `espeak-ng`, or
    a cloud API) — see references/getting-started.md
---

**WORKFLOW SKILL**

# Narrative Walkthrough

Produce a single narrated MP4 that actually matches what's on screen:
one continuous Playwright recording of **real** app interactions, fade
transitions between scenes (no jarring cuts), and TTS narration synced to
the video's **actual detected** scene changes — not to planned/logged
timestamps, which drift from wall clock. See
[references/recording-guide.md](references/recording-guide.md) and
[references/narration-sync.md](references/narration-sync.md) for full
detail; this file is the checklist.

## Steps

1. **Write the narration script first**, as data, not prose: a
   `narration-segments.json` array of `{id, text}` in scene order — one
   segment per scene the video will visit. This is the single source of
   truth driving both the recording (scene list) and the audio (TTS
   input). Never write a video from a human "recording checklist" —
   that's what produces mistimed cuts and screens that are described but
   never actually shown.
2. **Set up tools once**: confirm `ffmpeg`/`ffprobe`, a Playwright
   install + browser binary, and a TTS engine are available; install/
   start whatever is missing. Full setup and fallbacks:
   [references/getting-started.md](references/getting-started.md).
3. **Generate narration audio**: call the TTS engine once per segment,
   save `audio/<id>.wav`, and record each clip's real duration (via
   `ffprobe`) in `durations.json` — this drives scene pacing.
4. **Write and run the recording script** against the **real, live**
   target app (start it first if needed) — one continuous script, real
   clicks/typing/uploads, no manual cuts. Follow the scene-authoring
   rules (fade helper, pacing, dynamic selectors, avoiding the DOM-flood
   timing-drift bug) in
   [references/recording-guide.md](references/recording-guide.md), using
   [scripts/record-template.mjs](scripts/record-template.mjs) as a
   starting skeleton. Run it, producing a raw video and a `manifest.json`
   of logged (approximate) scene offsets.
5. **Derive real sync offsets from the rendered video** — never trust
   the logged manifest alone. Run ffmpeg scene-detection on the raw
   output, cluster the detected cuts, and map them onto the manifest's
   scene order; manually binary-search a few frames for any transition
   detection misses (e.g. dark-on-dark fades). Full method and script:
   [references/narration-sync.md](references/narration-sync.md) and
   [scripts/sync_offsets.py](scripts/sync_offsets.py).
6. **Build the audio track and mux the final video**: place each
   narration clip at its corrected real offset (`adelay`+`amix`), then
   mux with the full-length video (`libx264`/`aac`, `+faststart`) —
   never `-shortest` against a full-length video, or you'll clip the
   outro. Command reference:
   [references/narration-sync.md](references/narration-sync.md) and
   [scripts/build_audio_track.sh](scripts/build_audio_track.sh).
7. **Verify before delivering**: extract frames at each corrected scene
   offset and confirm visually that what's on screen matches that
   segment's narration text; check total duration is the full video
   length, not truncated.
8. **Clean up**: remove any script copies planted inside the target
   repo purely for `node_modules` resolution, stop/remove any TTS
   container you started, and note where build artifacts live if they
   need to persist beyond a temp directory.

## Example

> "Build a narrated walkthrough video of the checkout flow in this repo:
> browse products, add to cart, apply a coupon, and complete payment."

Write 5-6 narration segments matching those beats, generate TTS audio,
write a Playwright script that drives the real running app through each
beat with fade transitions, run it, detect real scene-cut offsets in the
output, build the synced audio track, mux, verify, deliver.

## Common issues

- **Narration/visual mismatch or screens claimed-but-never-shown**: the
  root cause is almost always recording from a human checklist instead
  of automating the same script that generates the narration. Fix by
  using the segment JSON to drive both.
- **Video's internal timeline drifts from wall clock** (scenes appear
  several seconds later than logged) — usually caused by a
  per-character/high-frequency DOM-mutation animation (e.g. a typing
  effect) flooding Chromium's screencast/CDP frame queue during
  recording. Batch such updates into chunks; still verify with real
  scene-detection regardless (step 5) since chunking only reduces, not
  eliminates, drift.
- **Hardcoded selectors/ids/filenames break on rerun**: the app's state
  changes each run (new rows, already-approved fields). Query the live
  app/API at runtime to pick the target dynamically instead of
  hardcoding ids.
- Full troubleshooting list (missing bundled browser, wrong app routes,
  `-shortest` truncation, etc.):
  [references/troubleshooting.md](references/troubleshooting.md).
