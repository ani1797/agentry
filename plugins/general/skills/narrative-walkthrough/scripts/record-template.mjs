// Generic skeleton for a narrative-walkthrough recording script.
// Copy this into a directory with `playwright` available in
// node_modules (see references/getting-started.md), fill in the
// TODOs, and run with plain `node`.
//
// Design: ONE continuous script, ONE browser page, real actions only.
// Every scene = hideScene -> real interaction -> markScene -> revealScene.

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const OUT_DIR = "/tmp/narrative-walkthrough/raw";
const APP_BASE = process.env.APP_BASE || "http://localhost:3000"; // TODO
const API_BASE = process.env.API_BASE || "http://localhost:8000"; // TODO
const durations = JSON.parse(
  fs.readFileSync("/tmp/narrative-walkthrough/durations.json", "utf8")
); // { "00-intro": <ms>, ... } from TTS clip lengths (see getting-started.md)

fs.mkdirSync(OUT_DIR, { recursive: true });

const OVERLAY_INIT = `
(function() {
  const d = document.createElement('div');
  d.id = '__fade';
  Object.assign(d.style, {
    position: 'fixed', inset: '0', background: '#05070d',
    opacity: '1', zIndex: '2147483647', transition: 'opacity 400ms linear',
    pointerEvents: 'none',
  });
  document.documentElement.appendChild(d);
})();`;

async function hideScene(page, ms = 400) {
  await page.evaluate(
    ({ ms }) => {
      let d = document.getElementById("__fade");
      if (!d) {
        d = document.createElement("div");
        d.id = "__fade";
        Object.assign(d.style, {
          position: "fixed", inset: "0", background: "#05070d",
          zIndex: "2147483647", pointerEvents: "none",
        });
        document.documentElement.appendChild(d);
      }
      d.style.transition = `opacity ${ms}ms linear`;
      d.style.opacity = "1";
    },
    { ms }
  );
  await page.waitForTimeout(ms);
}

async function revealScene(page, ms = 400) {
  await page.evaluate(
    ({ ms }) => {
      const d = document.getElementById("__fade");
      if (d) {
        d.style.transition = `opacity ${ms}ms linear`;
        d.style.opacity = "0";
      }
    },
    { ms }
  );
  await page.waitForTimeout(ms);
}

function markScene(recordStart, id) {
  manifest.push({ id, offsetMs: Date.now() - recordStart });
  console.log(`[scene] ${id} at ${((Date.now() - recordStart) / 1000).toFixed(2)}s`);
}

// Pace a scene's dwell time to at least its narration clip's duration,
// minus whatever real action time already elapsed.
async function pace(page, sceneStart, id, minFloorMs = 800) {
  const planned = durations[id] ?? minFloorMs;
  const already = Date.now() - sceneStart;
  await page.waitForTimeout(Math.max(minFloorMs, planned - already));
}

// TODO: replace with a real runtime lookup against your app's API so
// reruns don't break on stale hardcoded ids (see recording-guide.md).
async function pickDynamicTarget(apiBase) {
  const res = await fetch(`${apiBase}/some-list?pageSize=50`);
  const items = (await res.json()).items ?? [];
  return items.find((x) => /* TODO: matches what this scene needs */ true);
}

const manifest = [];

(async () => {
  const executablePath =
    process.env.CHROME_PATH ||
    ["/usr/sbin/google-chrome-stable", "/usr/bin/google-chrome",
      "/usr/bin/chromium-browser", "/usr/bin/chromium"]
      .find((p) => fs.existsSync(p));

  const browser = await chromium.launch({ executablePath });
  const context = await browser.newContext({
    recordVideo: { dir: OUT_DIR, size: { width: 1280, height: 720 } },
  });
  await context.addInitScript(OVERLAY_INIT);
  const page = await context.newPage();
  const recordStart = Date.now();

  // ---- 00 intro (TODO: title card, prop page, or first real screen) ----
  let t0 = Date.now();
  await page.goto(`${APP_BASE}/`);
  markScene(recordStart, "00-intro");
  await revealScene(page);
  await pace(page, t0, "00-intro");

  // ---- 01 ... add one block per narration segment ----
  await hideScene(page);
  t0 = Date.now();
  // TODO: real navigation/interaction for this scene
  markScene(recordStart, "01-example");
  await revealScene(page);
  await pace(page, t0, "01-example");

  // ---- final scene: hold, then close ----
  await hideScene(page);

  fs.writeFileSync(
    "/tmp/narrative-walkthrough/manifest.json",
    JSON.stringify(manifest, null, 2)
  );

  await context.close();
  await browser.close();
  console.log("DONE");
})();
