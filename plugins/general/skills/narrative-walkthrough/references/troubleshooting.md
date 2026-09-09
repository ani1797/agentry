# Troubleshooting

- **`Executable doesn't exist` / bundled Chromium missing** — Playwright's
  browser binary isn't downloaded. Run `npx playwright install chromium`
  if possible, otherwise launch with `executablePath` pointing at a
  system Chrome/Chromium (see getting-started.md).

- **`Cannot find module 'playwright'`** — the script isn't inside a
  directory whose `node_modules` (walking upward) contains the package.
  Copy the script into a subpackage that has it installed, run from
  there, delete the copy afterward.

- **A page 404s at the "obvious" URL** — don't assume; check the
  target app's actual route table. List/index pages are sometimes
  served at the app root rather than a named path with no separate
  index route existing.

- **Narration runs out before/after the scene it describes** — check
  `durations.json` against the real (corrected, post scene-detection)
  window available for that scene; a couple of seconds of overrun into
  the next scene is usually imperceptible and fine, but a large mismatch
  means either the scene needs a longer dwell time in the recording
  script or the narration segment needs tightening.

- **Video's internal timeline lags wall clock** — see the DOM-mutation
  screencast-flood note in recording-guide.md; batch heavy JS-driven DOM
  animation, and always verify with real scene-detection regardless.

- **Rerunning the recording script fails on a stale hardcoded id/
  selector** — the app's state changed since the id/filename was
  hardcoded (new rows created, that field already approved). Replace
  with a runtime lookup against the live app/API (see "dynamic
  selectors" in recording-guide.md).

- **Final mux is shorter than the recorded video** — you used
  `-shortest`, which truncates to the (typically shorter) audio track
  and clips the video's outro. Drop `-shortest` unless truncation is
  actually wanted.

- **Scene-detection misses a real transition** — usually a fade between
  two visually similar (e.g. both dark) scenes producing a small pixel
  delta. Lower the detection threshold for that region, or hand
  binary-search frames with `ffmpeg -ss <t> -frames:v 1` to pin the real
  offset.

- **White flash between scenes on a fresh cross-origin navigation** —
  the fade overlay div was only injected via `page.evaluate` (which
  doesn't survive a full navigation). Also register it via
  `page.addInitScript(...)` so it exists (and is opaque) before the new
  page's own content paints.

- **Leftover temp files in the target repo** — any script copied into
  the repo purely for `node_modules` resolution is not part of the app;
  delete it once the recording is finalized. Don't commit it.
