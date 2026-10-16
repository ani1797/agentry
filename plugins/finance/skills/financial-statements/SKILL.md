---
name: financial-statements
description: >
  Download bank, brokerage, and credit-card statements or transactions as
  per-account CSV/JSON files using the institution's portal. USE FOR: fetching,
  downloading, exporting, syncing statements from Wealthsimple or CIBC,
  adding support for another financial institution. DO NOT USE FOR: financial
  planning or investment advice; executing trades, transfers, or payments.
license: MIT
compatibility: Requires Python 3, Playwright MCP with browser_run_code_unsafe, and portal network access. The 1Password CLI is optional. See references/getting-started.md.
metadata:
  author: anirudh
  version: "1.0"
---

**WORKFLOW SKILL**

# Financial statements

Export records locally; never return credentials, tokens, or transaction
contents from browser scripts. Do not trade, transfer, or pay.

## Steps

1. Follow [workflow.md](references/workflow.md). Run commands from this
   skill's root, not the user's project directory:
   ```bash
   python3 scripts/bridge.py list
   ```
   Confirm institution and range: latest per open account or `--since`.
2. Discover optional 1Password credentials with `bridge.py find`; confirm
   the item before use. Otherwise let the user sign in manually. Never
   install 1Password, expose secrets, or bypass MFA.
3. Start the bridge and use its `run.login` / `run.download` loaders
   verbatim with Playwright. Pause for the user on `needs_user`.
4. Report per-account periods, row counts, paths, and errors, not private
   contents. Save outside repositories to `~/Documents/statements` by
   default. Stop the bridge and remove only this run's browser leftovers.

## Example

"Download my latest Wealthsimple statements as CSV and JSON." Confirm
latest-per-open-account, then follow the workflow. CIBC Online Banking is
also supported; Investor's Edge and PDF downloads are not implemented.

## Common issues

See [setup](references/getting-started.md) for missing prerequisites and
[workflow edge cases](references/workflow.md#edge-cases) for expired
sessions or an unreachable bridge. For an unsupported institution, use
[the adapter guide](references/ADDING_AN_INSTITUTION.md); never claim a
download succeeded before verifying the output.
