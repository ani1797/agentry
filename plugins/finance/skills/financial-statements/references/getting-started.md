# Statement downloader setup

Use Copilot CLI with Python 3 and a configured Playwright MCP server that
provides `browser_run_code_unsafe`. The plugin's `.mcp.json` is intentionally
empty: it does not install a browser service or change your MCP configuration.
See the [Playwright MCP project](https://github.com/microsoft/playwright-mcp)
for installation and configuration. The browser must be able to reach the
institution and the bridge on `127.0.0.1`; a browser running on a different
host cannot use this bridge without additional configuration.

Check `python3 --version`. If missing, install Python 3 through your OS package
manager or [python.org](https://www.python.org/downloads/). The bridge uses only
the Python standard library; no Python packages are required.

1Password is optional. If its `op` CLI is already installed, signed in, and
unlocked, the skill can discover matching Login items and ask which to use.
Otherwise, sign in to the institution manually in the browser. Do not install
1Password solely to run this skill. If you already use it and want CLI
integration, see [the official setup guide](https://developer.1password.com/docs/cli/get-started/).

From the skill root, list adapters without contacting any institution:

```bash
python3 scripts/bridge.py list
```

Supported adapters are CIBC Online Banking and Wealthsimple. Portal changes
can require updates; support does not guarantee every account type or export
will work. PDFs and CIBC Investor's Edge are not supported.

Downloads default to `~/Documents/statements/<institution>/`, with per-account
CSV/JSON files and a run manifest. CIBC uses masked account labels and card
cycle dates; Wealthsimple uses account IDs and monthly periods. Treat exports
as sensitive, keep them outside source control, and restrict local access.
Existing exports for the same account and period are overwritten.

Use `/financial-statements` separately from Plutus: the planner intentionally
has no financial-portal browser access. Its shell is for local modeling, not
credential retrieval. Afterwards, give Plutus the local paths you
want analyzed. If the user-level skill is also installed, disable or relocate
one copy yourself to avoid duplicate skill names; the plugin leaves it intact.
