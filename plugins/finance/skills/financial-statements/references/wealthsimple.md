# Wealthsimple

- Portal: https://my.wealthsimple.com/app/login
- Auth: email + password, then a **passkey** prompt. `login.js` clicks *Try another way*
  and lands on *Check your authenticator*, filling the TOTP from 1Password when the chosen item has one (otherwise `needs_user`). The code form
  auto-submits at 6 digits. Accounts using SMS/email 2FA get `needs_user` (the user types the code).
- Docs UI: https://my.wealthsimple.com/app/docs (Statements filter offers per-statement PDF + CSV).
  The UI's CSV is generated client-side from the GraphQL calls below; `download.js` reproduces it exactly.

## API

`POST https://my.wealthsimple.com/graphql` with headers
`authorization: Bearer <access_token>`, `x-ws-profile: trade`, `x-ws-api-version: 12`,
`x-ws-identity-id: <identity id>`.
The token is in the `_oauth2_access_v2` cookie (URL-encoded JSON: `access_token`,
`identity_canonical_id`, `expires_at`, ...). It's read inside the browser process only.

| Purpose | Query | Key args |
|---|---|---|
| Accounts | `identity(id){ accounts(first, filter:{}) { edges { node { id nickname unifiedAccountType currency status custodianAccounts{id} }}}}` | |
| Statement index | `identity(id){ documents(limit, offset, categories:["performance"], locale) { total_count results { period frequency type account{id type} }}}` | `type` ∈ `brokerage`, `cash`, `credit_card` |
| Brokerage/cash statement | `monthlyStatement(accountId, period, statementType)` → `data { ... on CashMonthlyStatementObject / BrokerageMonthlyStatementObject { currentTransactions, activitiesPerCurrency } }` | `statementType = <type>_monthly_statement`, `period = YYYY-MM-01` |
| Credit-card statements in a month | `creditCardAccount(id){ statements(startDate, endDate){ id statementDate } }` | |
| Credit-card statement | `creditCardAccount(id){ statement(id){ ...summary, transactions{ amount postDate transactionDate type details } } }` | |

## CSV columns (match the UI export)

- Brokerage / cash: `date, transaction, description, amount, balance, currency`
- Credit card: `transaction_date, post_date, type, details, amount, currency`

The `.json` file next to each CSV holds the full statement payload (credit-card summary,
APR, balances, custodian ids) for anything the CSV leaves out.

## Known gaps / ideas

- PDFs aren't downloaded (documents have `s3Key` but no `downloadUrl`; the UI fetches a signed URL on click).
  If needed, click the `PDF <name>` button and capture `page.waitForEvent('download')`, then PUT the bytes to the bridge.
- Account labels come from the nickname or a `unifiedAccountType` → label map in `download.js`. Add new types there.
