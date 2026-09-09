# Recording guide

The recording script is a **single continuous Playwright script**, not a
sequence of independent clips stitched together in an editor. It drives
one `page` through every scene in narration order, against the real
running target app (start it first — `docker compose up`, `npm run dev`,
etc. — and wait until it responds before launching the browser).

## Skeleton

Start from [record-template.mjs](../scripts/record-template.mjs). Core
pieces:

```js
const context = await browser.newContext({
  recordVideo: { dir: OUT_DIR, size: { width: 1280, height: 720 } },
});
const page = await context.newPage();
const recordStart = Date.now();
const manifest = [];

function markScene(recordStart, id) {
  manifest.push({ id, offsetMs: Date.now() - recordStart });
}
```

## Fade transitions (no jarring cuts)

Inject a full-viewport overlay div and toggle its opacity via
`page.evaluate`, wrapping every scene boundary:

```js
async function hideScene(page, ms = 400) { /* fade #__fade to opacity 1 */ }
async function revealScene(page, ms = 400) { /* fade #__fade to opacity 0 */ }
```

Also register the same overlay-injection script via
`page.addInitScript(...)` so it's already present (and opaque) the
instant any **fresh full navigation** happens (a `page.goto` to a new
origin, e.g. a cross-origin admin tool) — otherwise you get a white
flash-of-unstyled-content before the overlay script has a chance to run.

Sequence for every scene transition: `hideScene` → do the navigation/
interaction that changes what's on screen → wait for the new content to
be ready → `markScene(...)` → `revealScene`.

## Pacing each scene to its narration

Look up each scene's TTS clip duration from `durations.json` and make
sure the scene stays on screen at least that long, accounting for real
action latency (network round-trips, page loads) that already ate into
the budget:

```js
const already = Date.now() - sceneStart;
await page.waitForTimeout(Math.max(minFloorMs, plannedMs - already));
```

Never pad with a long **static** hold — if there's spare time, use it
for a small, real, visually-meaningful action (scroll to the element
being discussed, hover a card, expand a filter) so "what's being said"
and "what's shown" stay aligned. A screen that sits static for 20+
seconds while narration talks about it, or narration that claims a
screen was scrolled/interacted with when it wasn't, are exactly the
defects this skill exists to eliminate.

## "Show it, don't say it" — visible-action rule

If narration says a row/screen/state is visible, the script must
actually navigate/scroll/filter to make it visible on screen at that
moment — don't rely on the viewport already happening to contain it.
Prefer real interactions (`scrollIntoViewIfNeeded`, filling a filter
input, clicking a tab) over hoping the layout lines up.

## Use real data, not fabricated content

Prefer driving genuinely live app state (real uploads via
`setInputFiles`, real API responses, real logs) over faking content in
markup. For scenes that need to show something like terminal/log output
that would be noisy or slow to render live character-by-character in the
main app UI, it's fine to build a small static HTML "prop" page (see
`assets/` templates) — but populate it with **real** captured output
(actual `curl`/log lines from the real system), not invented text.

## Dynamic selectors — never hardcode ids that a rerun will invalidate

Any target picked by a previous run (a specific job id, an "unreviewed"
row, a specific filename) will likely no longer match on a rerun,
because the app's own state changed (new rows created, that field
already approved, list pagination shifted). Query the live app/API at
the start of the relevant scene to pick a valid target dynamically:

```js
async function pickTarget(apiBase) {
  const res = await fetch(`${apiBase}/some-list?pageSize=50`);
  const items = (await res.json()).items;
  return items.find(matchesWhatThisSceneNeeds);
}
```

Then navigate directly (`page.goto` to the resolved URL) rather than
scrolling/clicking through a table row that might not exist or might be
off-screen — more robust and still wrapped in the fade helpers.

## Avoid the DOM-mutation screencast flood (timing-drift bug)

A prop page with a per-character "typing" animation (one `textContent`
update per keystroke, driven by a fast `setInterval`) generates a very
high rate of DOM mutations. When that page is being recorded by
Playwright's `recordVideo`, this can overwhelm Chromium's internal
screencast/CDP frame-delivery queue, causing the **recorded video's**
internal timeline to lag increasingly behind wall clock — by several
seconds after a couple of such scenes. Symptoms: extracting an accurate
frame (`-ss` **after** `-i` in ffmpeg) at a scene's logged manifest
offset still shows the *previous* scene.

Mitigate by batching updates (e.g. 5 characters per repaint instead of
1, with a minimum per-chunk delay) rather than eliminating the effect
entirely — animation gives visual life to what would otherwise be a
static hold, but batching sharply reduces repaint frequency.

**Do not rely on chunking alone.** Always verify final sync using real
scene-detection on the rendered output (see
[narration-sync.md](narration-sync.md)) — this catches any residual
drift regardless of its cause.

## Common environment fixes

- Node can't find `playwright`: copy the script into a directory that
  has it in `node_modules` (see getting-started.md), run with plain
  `node`, delete the copy afterward.
- Bundled Chromium missing: launch with `executablePath` pointing at a
  system browser.
- A route 404s: don't assume the intuitive URL — check the app's actual
  routing (e.g. its `app/` or `pages/` or router config) for where a
  page is really served; a list page is sometimes at the app root `/`
  rather than a named path.
