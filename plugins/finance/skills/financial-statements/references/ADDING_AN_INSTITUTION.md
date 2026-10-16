# Adding an institution

Each institution is a directory `institutions/<id>/` (`<id>` = lowercase, hyphens):

```
institutions/<id>/
├── institution.json   # metadata + optional credential-search keywords
├── login.js           # async (page) => {status: "logged_in" | "needs_user", step, detail}
└── download.js        # async (page) => {ok, out, count, results:[{account, period, rows, files} | {error}]}
```

Start by copying `institutions/_template/`. Any extra `*.js` in the directory is also
served (as `run.<name>`), which is useful for helpers such as `discover.js`.

## institution.json

| key | meaning |
|---|---|
| `name` | Display name |
| `login_url` | Portal login page |
| `op_match` | Optional lower-case institution keywords/domains (e.g. `["example.com","example"]`) used by `find` to search 1Password Login titles/URLs, along with the `login_url` domain. **Never** put item names, IDs or vault names here |
| `strategy` | `api` (preferred) or `ui` |
| `formats` | Formats produced, e.g. `["csv","json"]`, `["ofx"]`, `["qfx"]` |

## Contract for the JS files

- Each file is a single expression: `async (page) => { ... }`. Comments above it are fine.
- `__BRIDGE_URL__` is replaced by the bridge base URL. Use `page.request` (not `fetch` in
  the page) to reach it:
  - `GET  /config` → `{institution, out, since, has_credentials, has_otp}`
  - `GET  /secret/username`, `/secret/password`, `/secret/<field label or id>` (each served once)
  - `GET  /otp` → current TOTP
  - `PUT  /file?path=<account-folder>/<YYYY-MM>.csv` with the body as the file contents
  - `POST /log` → append to `<out>/.bridge.log`
- **Never return secrets, tokens or transaction contents** in the result. Return only a summary.
- 1Password is optional. When `has_credentials` is false, return
  `{status:"needs_user", step:"credentials", detail:"No stored credentials; ask the user to sign in in the browser window."}`.
  The same applies if `/secret/*` or `/otp` returns a non-200 response.
- Write one folder per account: `<label-slug>__<stable-account-id>/<YYYY-MM>.<ext>`, plus
  `manifest-<YYYY-MM-DD>.json`.
- Honour `cfg.since` (all periods on/after it). Otherwise fetch the latest statement per open account.
- The bridge re-reads the JS on every `run.*` call, so you can edit and re-run without restarting it
  (but restart before re-running a login: each secret is served only once).

## Sandbox gotchas (`browser_run_code_unsafe`)

- No `require`/`import`, `Buffer`, `TextDecoder` or `URLSearchParams`. `eval`, `encodeURIComponent`,
  `escape`, `JSON` and Playwright APIs work.
- Build query strings by hand: `Object.entries(p).map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&')`.
- Read a browser download as text without Buffer:
  ```js
  let bin = ''; for await (const c of await download.createReadStream()) for (let i = 0; i < c.length; i++) bin += String.fromCharCode(c[i]);
  const text = decodeURIComponent(escape(bin)); // UTF-8 decode
  ```
- Some export endpoints only work as a real navigation (see CIBC): submit a hidden `<form>` via
  `page.evaluate` and await `page.waitForEvent('download')`.
- Tokens are often JSON-encoded in storage (`"abc"`): `JSON.parse` them before use.

## Discovering the fastest path (do this with the Playwright MCP)

1. Log in manually or with a draft `login.js`. Open the statements/documents page.
2. Record network traffic while clicking a statement's CSV/OFX/QFX/"Download" button:
   ```js
   async (page) => { const ops = []; const h = async r => { const q = r.request();
     if (/graphql|api|statement|export|download/i.test(q.url())) ops.push({ url: q.url(), method: q.method(),
       body: q.postData()?.slice(0, 1500), status: r.status(), ct: r.headers()['content-type'] }); };
     page.on('response', h); const dl = page.waitForEvent('download', { timeout: 15000 }).catch(() => null);
     await page.getByRole('button', { name: 'CSV' }).first().click(); const d = await dl;
     page.off('response', h); return { file: d?.suggestedFilename(), ops }; }
   ```
3. If the download is a `blob:` URL, the CSV is built client-side. Replay the JSON API it used
   (see `wealthsimple/download.js`). If it's a server URL, `page.request.get()` it with the
   session cookies and PUT the bytes to the bridge.
4. Find the auth token: check `cookies()`, `localStorage`, or the request's `authorization` header
   (from `request.allHeaders()`). Read it only inside `download.js`.
5. Last resort (UI-only portals): loop over accounts in the UI, click Download, then
   `const d = await page.waitForEvent('download'); const buf = await (await d.createReadStream())...`
   or read via `d.path()`, then PUT to the bridge.
6. Verify: compare one generated file against the portal's own export (`diff`).
7. Add a row to the *Supported institutions* table in `SKILL.md` and write
   `references/<id>.md` with the API notes.
