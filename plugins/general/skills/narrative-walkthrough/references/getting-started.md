# Getting started

## Required tools

| Tool | Purpose | Check |
|---|---|---|
| `ffmpeg` / `ffprobe` | scene detection, audio mixing, muxing, verification frame extraction | `ffmpeg -version` |
| Node.js + `playwright` (or `@playwright/test`) | drives the real browser recording | see below |
| A TTS engine | turns narration text into audio clips | see below |

If any target repo already depends on `playwright`/`@playwright/test`
(check its `package.json`), reuse that install instead of adding a new
dependency — do not add new npm dependencies just for this skill unless
nothing is available.

## Playwright browser binary

Playwright's own bundled Chromium is often **not downloaded** in CI/dev
sandboxes even when the npm package is installed. Check:

```bash
ls ~/.cache/ms-playwright/ 2>/dev/null
```

If empty/missing, either:

- `npx playwright install chromium` (best, if network/disk allows), or
- launch with an existing system browser instead:
  ```js
  const browser = await chromium.launch({
    executablePath: "/usr/bin/google-chrome" // or google-chrome-stable,
                                              // chromium-browser, etc.
  });
  ```
  Find a candidate path with `which google-chrome google-chrome-stable
  chromium chromium-browser 2>/dev/null`, or check the target repo's own
  Playwright config for a `chromeExecutablePath`/candidate list it
  already uses.

No X server/Xvfb is needed for headless recording — Playwright's
`context.recordVideo` captures frames via Chromium's own internal
screencast/CDP mechanism, not a real display server.

## Node module resolution gotcha

Node resolves `node_modules` by walking up from the **script's own
directory**, not the current working directory. If your recording script
lives in a scratch directory (e.g. `/tmp/narrative-walkthrough/`) but
`playwright` is only installed inside a target repo's subpackage (e.g.
`apps/web/node_modules`), copy the script into that subpackage
temporarily before running it with plain `node`, and delete the copy
afterward — it is not part of the app and must not be committed.

## TTS engine options

Any of these work; pick whichever is already available:

- **Local Kokoro-FastAPI** (good default, no cloud dependency, no GPU
  required): run once via Docker —
  ```bash
  docker run -d --name narration-tts -p 8880:8880 \
    ghcr.io/remsky/kokoro-fastapi-cpu:latest
  ```
  Generate a clip:
  ```bash
  curl -s http://localhost:8880/v1/audio/speech \
    -H "Content-Type: application/json" \
    -d '{"model":"kokoro","input":"<segment text>","voice":"af_heart","response_format":"wav"}' \
    -o audio/<id>.wav
  ```
  `af_heart` is a good default voice (graded "A" quality). This engine
  is **TTS only** — it cannot transcribe existing audio/video.
- **OS-level CLI TTS** (`say` on macOS, `espeak-ng`/`spd-say` on Linux)
  when no Docker/network is available — lower quality but zero setup.
- **A cloud TTS API** if the project already has credentials for one —
  prefer this over adding new paid dependencies without asking the user.

Whatever engine you use, always compute each clip's **real** duration
afterward via `ffprobe` rather than estimating from text length — narration
pacing in the recording script depends on exact durations:

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio/00-intro.wav
```

Stop/remove any container you started for this purpose once the final
video is delivered, unless the user wants it kept running.
