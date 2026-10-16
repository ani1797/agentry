# Financial statements downloader

Downloads statements **per account** in structured form (CSV + raw JSON) into
`~/Documents/statements/<institution>/<account-label>__<account-id>/<YYYY-MM>.{csv,json}`
plus a `manifest-<date>.json` per run.

## How it works

The Playwright MCP sandbox can't run `op` or write files, but it *can* make HTTP
requests. `scripts/bridge.py` runs a token-protected localhost server that:

- if 1Password is available and the user picked an item, reads it **inside the bridge**, so usernames, passwords and OTPs never appear in the transcript;
- serves the institution's `login.js` / `download.js` (from `institutions/<id>/`);
- accepts statement files from the browser and writes them to the output directory.

Prefer API calls made with the logged-in session (fast, exact) over clicking through the UI.
Only fall back to UI clicks / `page.waitForEvent('download')` when no API exists.

## Workflow

Run all commands from the skill root (the parent of this `references/`
directory), or use absolute paths to the bundled scripts.

1. **Ask which institution.** Run `python3 scripts/bridge.py list`. If the institution isn't
   listed, follow [ADDING_AN_INSTITUTION.md](ADDING_AN_INSTITUTION.md) first.
   Also confirm the range: latest statement per open account (default) or `--since YYYY-MM-DD`.

2. **Credentials (1Password is optional).** Run `python3 scripts/bridge.py find <institution>`.
   It never fails and never prints secrets. It returns `{"op": <status>, "items": [...]}`.
   Item IDs, titles and vaults are **never** hardcoded; they are discovered here at runtime.
   - `op` = `available` and **one** item matches: confirm it with the user and pass its `id` as `--op-item`.
   - `available` and **several** items match: show title + vault and ask which one (or none).
   - `available` and **no** items match: ask whether a differently-named item exists. Re-run with
     `--query <word>` if so; otherwise log in manually.
   - `not_installed` / `no_account`: don't mention or install 1Password. Use manual login (omit `--op-item`).
   - `locked` / `error`: say 1Password couldn't be read. Offer to unlock it and retry, or log in manually.
   Manual login means the user signs in themselves in the opened browser window.

3. **Start the bridge** (bash, `mode: "async"`):
   ```bash
   python3 scripts/bridge.py serve <institution> [--op-item <id>] [--since YYYY-MM-DD] [--out ~/Documents/statements]
   ```
   Read its single JSON line: `run.login`, `run.download`, `login_url`, `out`,
   `has_credentials`, `credentials`. If `--op-item` was given but 1Password became unavailable,
   the bridge still starts with `has_credentials: false`; continue with manual login.

4. **Open the portal and log in.** Call `playwright-browser_navigate` with `login_url`, then
   `playwright-browser_run_code_unsafe` with `code` = `run.login` **verbatim**.
   - `{"status":"logged_in"}`: continue.
   - `{"status":"needs_user", ...}`: tell the user what's needed (2FA code, passkey, captcha,
     or a manual login) and ask them to finish in the open browser window. Then
     re-run `run.login` (it returns `already` once logged in).
   - Never type secrets with `browser_type`/`browser_fill_form`; always go through the bridge.
     Each secret is served **once** per bridge run, so restart the bridge before retrying a login.

5. **Download per account.** Run `run.download` the same way. It returns a summary
   (`account`, `period`, `rows`, `files`, or `error`). Report this table to the user.
   Errors are also appended to `<out>/.bridge.log`.

6. **Clean up.** Stop the bridge shell (it also exits after `--ttl`, 900 s by default).
   Close the browser if the user is done.

## Supported institutions

| id | Strategy | Formats | Notes |
|----|----------|---------|-------|
| `wealthsimple` | GraphQL API via session cookie | CSV, JSON | [wealthsimple.md](wealthsimple.md) |
| `cibc` | REST API + native CSV export (Online Banking only) | CSV, JSON | [cibc.md](cibc.md) |

## Edge cases

- **Session expiry mid-run**: re-run `run.login`; downloads are idempotent (files are overwritten).
- **Bridge unreachable**: the loader throws `bridge unreachable`. Restart `serve` and use the new `run.*` strings (token and port change each run).
- **MCP `filename` argument**: don't use it; it is restricted to the MCP's own roots. Use the `run.*` loader strings.
- **Closed accounts** are skipped in "latest" mode but included with `--since`.
- **Empty statements** still produce a CSV with only a header row (e.g. no activity that month).
- **Multiple 1Password matches** (e.g. separate banking and brokerage logins for the same institution): ask the user which item to use. Never guess.
- **No 1Password**: everything works without it. `login.js` returns `needs_user` and the user signs in by hand.
- **Browser-download leftovers**: the Playwright MCP also keeps a copy of browser downloads (e.g. `cibc.csv`)
  in its own `.playwright-mcp/` output directory. Delete them after the run.
