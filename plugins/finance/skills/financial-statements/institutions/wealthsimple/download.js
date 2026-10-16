// Wealthsimple statement downloader (API strategy).
// Run via browser_run_code_unsafe { filename: <scripts.download> } after login.js reports logged_in.
// Writes <out>/<account-folder>/<period>.csv and .json through the bridge and returns a summary
// (no transaction contents, no tokens).
async (page) => {
  const BRIDGE = '__BRIDGE_URL__';
  const GQL = 'https://my.wealthsimple.com/graphql';
  const cfg = await (await page.request.get(`${BRIDGE}/config`)).json();
  const log = (m) => page.request.post(`${BRIDGE}/log`, { data: `[wealthsimple] ${new Date().toISOString()} ${m}` }).catch(() => {});

  const readToken = async () => {
    const ck = (await page.context().cookies('https://my.wealthsimple.com')).find(c => c.name === '_oauth2_access_v2');
    if (!ck) return null;
    return JSON.parse(decodeURIComponent(ck.value));
  };
  let tok = await readToken();
  if (!tok) return { ok: false, error: 'Not logged in (no _oauth2_access_v2 cookie). Run login.js first.' };
  if (tok.expires_at && tok.expires_at * 1000 < Date.now() + 60000) {
    await page.reload(); await page.waitForTimeout(4000); tok = await readToken();
  }
  const identityId = tok.identity_canonical_id;

  const gql = async (operationName, query, variables) => {
    const r = await page.request.post(GQL, {
      headers: {
        authorization: `Bearer ${tok.access_token}`, 'content-type': 'application/json',
        'x-ws-profile': 'trade', 'x-ws-api-version': '12', 'x-ws-locale': 'en-CA', 'x-ws-identity-id': identityId,
      },
      data: { operationName, query, variables },
    });
    const body = await r.json().catch(() => null);
    if (r.status() !== 200 || !body || body.errors) throw new Error(`${operationName}: HTTP ${r.status()} ${JSON.stringify(body?.errors || '').slice(0, 300)}`);
    return body.data;
  };
  const put = async (path, content) => {
    const r = await page.request.put(`${BRIDGE}/file?path=${encodeURIComponent(path)}`, { data: content });
    if (!r.ok()) throw new Error(`bridge write failed for ${path}: ${r.status()}`);
    return (await r.json()).saved;
  };
  const csv = (header, rows) => [header, ...rows].map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n') + '\n';

  // ---- accounts --------------------------------------------------------------------------
  const LABELS = {
    CASH: 'Chequing', CASH_USD: 'USD savings', HISA_PORTFOLIO_NON_REGISTERED: 'Savings', CREDIT_CARD: 'Credit card',
    SELF_DIRECTED_TFSA: 'TFSA', SELF_DIRECTED_RRSP: 'RRSP', SELF_DIRECTED_SPOUSAL_RRSP: 'Spousal RRSP', SELF_DIRECTED_FHSA: 'FHSA',
    SELF_DIRECTED_LIRA: 'LIRA', SELF_DIRECTED_RRIF: 'RRIF', SELF_DIRECTED_RESP_FAMILY: 'RESP',
    SELF_DIRECTED_NON_REGISTERED: 'Non-registered', SELF_DIRECTED_NON_REGISTERED_MARGIN: 'Margin',
    SELF_DIRECTED_NON_REGISTERED_PREDICTIONS: 'Predictions', SELF_DIRECTED_CRYPTO: 'Crypto', BUSINESS_CHEQUING: 'Business chequing',
  };
  const accData = await gql('FetchAccounts', `query FetchAccounts($id: ID!) { identity(id: $id) { accounts(first: 200, filter: {}) {
    edges { node { id nickname unifiedAccountType currency status type custodianAccounts { id } } } } } }`, { id: identityId });
  const accounts = Object.fromEntries(accData.identity.accounts.edges.map(({ node: a }) => {
    const nick = (a.nickname || '').replace(/[^\p{L}\p{N} ._-]/gu, '').trim();
    const label = nick || LABELS[a.unifiedAccountType] || a.unifiedAccountType.toLowerCase().replace(/_/g, ' ');
    const slug = `${label}`.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    return [a.id, { ...a, label, folder: `${slug}__${a.id}` }];
  }));

  // ---- statement index -------------------------------------------------------------------
  const docs = [];
  for (let offset = 0; ; offset += 100) {
    const d = await gql('FetchDocs', `query FetchDocs($id: ID!, $offset: Int) { identity(id: $id) {
      documents(limit: 100, offset: $offset, categories: ["performance"], locale: "en-CA") { total_count results { id period frequency type account { id type } } } } }`,
      { id: identityId, offset });
    const page_ = d.identity.documents;
    docs.push(...page_.results);
    if (!page_.results.length || docs.length >= page_.total_count) break;
  }
  const monthly = docs.filter(d => d.frequency === 'month' && d.account?.id && d.period);

  let selected;
  if (cfg.since) {
    selected = monthly.filter(d => d.period >= cfg.since.slice(0, 7) + '-01');
  } else {
    const latest = {};
    for (const d of monthly) {
      if (accounts[d.account.id]?.status !== 'open') continue;
      if (!latest[d.account.id] || d.period > latest[d.account.id].period) latest[d.account.id] = d;
    }
    selected = Object.values(latest);
  }
  const seen = new Set();
  selected = selected.filter(d => { const k = `${d.account.id}|${d.period}|${d.type}`; if (seen.has(k)) return false; seen.add(k); return true; });

  // ---- fetchers ----------------------------------------------------------------------------
  const MONTHLY_Q = `query FetchMonthlyStatementWithTransactions($accountId: String!, $period: String!, $statementType: StatementType!) {
    monthlyStatement(accountId: $accountId, period: $period, statementType: $statementType) {
      id statementType statementKey createdAt
      data { __typename
        ... on CashMonthlyStatementObject { custodianAccountId currentTransactions { transactionDate transactionType description cashMovement balance } }
        ... on BrokerageMonthlyStatementObject { custodianAccountId isMultiCurrency
          currentTransactions { transactionDate transactionType description cashMovement balance unit }
          activitiesPerCurrency { currency currentTransactions { transactionDate transactionType description cashMovement balance unit } } }
      } } }`;
  const CC_LIST_Q = `query FetchCreditCardStatements($creditCardAccountId: ID!, $endDate: ISO8601Date, $startDate: ISO8601Date) {
    creditCardAccount(id: $creditCardAccountId) { id statements(endDate: $endDate, startDate: $startDate) { id statementDate statementOpenDate statementCloseDate } } }`;
  const CC_Q = `query FetchCreditCardStatement($accountCanonicalId: ID!, $statementId: ID!) { creditCardAccount(id: $accountCanonicalId) { id statement(id: $statementId) {
    id statementDate statementOpenDate statementCloseDate paymentDueDate minimumPaymentDue minimumPaymentOutstanding annualPercentageRate
    annualCashAdvancePercentageRate previousStatementBalance summaryOtherCredits summaryTotalCredits summaryPurchases summaryCashAdvances
    summaryInterest summaryFees summaryTotalDebits summarySubtotal statementBalance summaryPayments paymentStatus statementBalanceOutstanding
    creditLine isPaidFully transactions { id amount postDate transactionDate description type details } } } }`;
  const endOfMonth = (p) => { const [y, m] = p.split('-').map(Number); return new Date(Date.UTC(y, m, 0)).toISOString().slice(0, 10); };
  const titleCase = (s) => (s || '').toLowerCase().replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase());

  const results = [];
  for (const d of selected) {
    const acct = accounts[d.account.id] || { label: d.account.type, folder: d.account.id, currency: '' };
    const base = `${acct.folder}/${d.period.slice(0, 7)}`;
    try {
      if (d.type === 'credit_card') {
        const list = (await gql('FetchCreditCardStatements', CC_LIST_Q, { creditCardAccountId: d.account.id, startDate: d.period, endDate: endOfMonth(d.period) })).creditCardAccount.statements;
        for (const s of list) {
          const st = (await gql('FetchCreditCardStatement', CC_Q, { accountCanonicalId: d.account.id, statementId: s.id })).creditCardAccount.statement;
          const rows = st.transactions.map(t => [t.transactionDate, t.postDate, titleCase(t.type), t.details || t.description, t.amount, acct.currency || 'CAD']);
          const name = list.length > 1 ? `${acct.folder}/${st.statementDate}` : base;
          await put(`${name}.csv`, csv(['transaction_date', 'post_date', 'type', 'details', 'amount', 'currency'], rows));
          await put(`${name}.json`, JSON.stringify({ account: acct, document: d, statement: st }, null, 2));
          results.push({ account: acct.label, accountId: d.account.id, period: d.period, statementDate: st.statementDate, rows: rows.length, files: [`${name}.csv`, `${name}.json`] });
        }
        continue;
      }
      const statementType = `${d.type}_monthly_statement`;
      const st = (await gql('FetchMonthlyStatementWithTransactions', MONTHLY_Q, { accountId: d.account.id, period: d.period, statementType })).monthlyStatement;
      if (!st?.data) { results.push({ account: acct.label, accountId: d.account.id, period: d.period, skipped: 'no statement data' }); continue; }
      const cur = (u) => (u && u.startsWith('$') ? u.slice(1) : acct.currency);
      let tx = [];
      if (st.data.isMultiCurrency && st.data.activitiesPerCurrency?.length) {
        for (const g of st.data.activitiesPerCurrency) tx.push(...g.currentTransactions.map(t => ({ ...t, unit: t.unit || `$${g.currency}` })));
      } else tx = st.data.currentTransactions || [];
      const rows = tx.map(t => [t.transactionDate, t.transactionType, t.description, t.cashMovement, t.balance, cur(t.unit)]);
      await put(`${base}.csv`, csv(['date', 'transaction', 'description', 'amount', 'balance', 'currency'], rows));
      await put(`${base}.json`, JSON.stringify({ account: acct, document: d, statement: st }, null, 2));
      results.push({ account: acct.label, accountId: d.account.id, period: d.period, rows: rows.length, files: [`${base}.csv`, `${base}.json`] });
    } catch (e) {
      await log(`error ${d.account.id} ${d.period}: ${e.message}`);
      results.push({ account: acct.label, accountId: d.account.id, period: d.period, error: e.message.slice(0, 300) });
    }
  }

  const manifest = { institution: 'wealthsimple', generatedAt: new Date().toISOString(), mode: cfg.since ? `since ${cfg.since}` : 'latest', out: cfg.out, results };
  await put(`manifest-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(manifest, null, 2));
  await log(`done: ${results.length} statements`);
  return { ok: !results.some(r => r.error), out: cfg.out, count: results.length, results };
}
