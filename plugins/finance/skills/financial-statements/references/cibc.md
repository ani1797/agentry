# CIBC Online Banking

- Portal: https://www.cibconline.cibc.com/ebm-resources/online-banking/client/index.html#/auth/signon
  (redirects to `secure.cibc.com` for sign-on).
- Credentials (optional, from 1Password if available): the `username` field = full card
  number, plus `password`. If several items match, ask the user which one is for Online Banking.
- Auth flow handled by `login.js`:
  1. Cookie banner, then **Accept all cookies**.
  2. Card step: either a remembered-card list (picks the checkbox whose label ends in the
     username's last 4 digits, else *Sign on with a different card*) or a *Card number* textbox.
  3. Password page, then **Sign on**.
  4. One-time verification code (OTVC) by SMS/email/app: returns `needs_user` (the item has no TOTP).
     Remembered/trusted browsers usually skip this.
  5. Promo interstitials: clicks *Remind me later* / *No thanks* / *Skip*.
- Investor's Edge (brokerage) is a separate portal and is **not** covered by this adapter.

## API (all under `https://www.cibconline.cibc.com/ebm-ai/api`)

Headers: `x-auth-token: <token>`, `brand: cibc`, `client-type: default_web`,
`x-requested-with: XMLHttpRequest`. Token = `JSON.parse(sessionStorage['ebanking:session_token'])`.

| Purpose | Request | Notes |
|---|---|---|
| Accounts | `GET /v2/json/accounts` | `id` (64-hex), `number` (masked), `nickname`, `categorization.subCategory` (`CHEQUING`, `SAVINGS`, `CREDIT_CARD`, `PERSONAL_LINE_CREDIT`, `ISI`...), `status`, `capabilities` (`DOWNLOAD_TRANSACTIONS`) |
| Card statement date | `GET /v1/json/accountDetails/{id}` | `details.statementDate`, `statementBalance`, `minPaymentDueAmount`, `nextPaymentDueDate`... |
| Transactions (JSON) | `GET /v1/json/transactions?accountId&filterBy=range&fromDate&toDate&limit=150&offset&sortAsc=true&sortByField=date[&ccTransactionState=both]` | `meta.hasNext` paging. **422 = no transactions** |
| CSV export, step 1 | `POST /v1/json/downloadTransactions` body `{"downloadTransaction":{"accountId","criteria":"DATE_RANGE","format":"CSV","fromDate","toDate"}}`, `accept`/`content-type: application/vnd.api+json` | returns `fileUri`. **422 with problem code `0121` = no transactions** |
| CSV export, step 2 | `POST /v1/json/downloadTransactions/file/{fileUri}?eb-target-site=ebkpce`, form field `X-Auth-Token` | **Must be a real browser form navigation.** `page.request`/`fetch` get HTTP 500. `download.js` submits a hidden form and reads the `download` event stream |

Other `format` values the UI offers: Microsoft Money, QuickBooks, Quicken, Sage 50 (OFX/QFX/QBO variants).

## Periods

- **Credit card**: statement cycles end on `statementDate`. The latest is
  `(statementDate − 1 month + 1 day) .. statementDate`, and files are named `<statementDate>.csv`.
- **Deposit accounts / line of credit**: calendar months (`YYYY-MM.csv`). The latest is the last complete month.
  Accounts on yearly paper statements still get monthly files.
- `--since`: every period whose end date is on/after the given date.
- CIBC excludes today and the previous 2 business days from exports, which only matters for ranges ending near today.

## CSV columns

CIBC exports have no header; `download.js` prepends one:
- Deposit / LOC: `date,description,debit,credit`
- Credit card: `date,description,debit,credit,card_number` (card number is masked by CIBC)

The `.json` beside each CSV holds the transactions API output (posted date, merchant category,
`fitId`, pending flag) and, for the latest card cycle, the card's statement summary.

## Skipped

- `ISI` investment accounts (no `DOWNLOAD_TRANSACTIONS` capability).
- `INACTIVE` accounts in latest mode (included with `--since`).
