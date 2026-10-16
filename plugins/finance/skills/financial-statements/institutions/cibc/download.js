// CIBC Online Banking statement downloader (API strategy).
// Run via the bridge loader (`run.download`) after login.js reports logged_in.
// For each account: CIBC's native CSV export for the statement period (+ header row) and the
// richer JSON from the transactions API. Returns a summary only (no transactions, no tokens).
async (page) => {
  const BRIDGE = '__BRIDGE_URL__';
  const API = 'https://www.cibconline.cibc.com/ebm-ai/api';
  const cfg = await (await page.request.get(`${BRIDGE}/config`)).json();
  const log = (m) => page.request.post(`${BRIDGE}/log`, { data: `[cibc] ${new Date().toISOString()} ${m}` }).catch(() => {});
  const put = async (path, content) => {
    const r = await page.request.put(`${BRIDGE}/file?path=${encodeURIComponent(path)}`, { data: content });
    if (!r.ok()) throw new Error(`bridge write failed for ${path}: ${r.status()}`);
  };

  if (!page.url().includes('cibconline.cibc.com')) return { ok: false, error: 'Not on CIBC Online Banking. Run login.js first.' };
  const raw = await page.evaluate(() => sessionStorage.getItem('ebanking:session_token'));
  if (!raw) return { ok: false, error: 'No session token in sessionStorage. Run login.js first.' };
  const tok = raw.startsWith('"') ? JSON.parse(raw) : raw;
  const H = { 'x-auth-token': tok, brand: 'cibc', 'client-type': 'default_web', accept: 'application/json', 'x-requested-with': 'XMLHttpRequest' };
  const getJson = async (url) => {
    const r = await page.request.get(url, { headers: H });
    if (!r.ok()) throw new Error(`GET ${url.split('?')[0].replace(/[0-9a-f]{64}/g, '<id>')}: HTTP ${r.status()}`);
    return r.json();
  };

  // ---- dates ---------------------------------------------------------------------------------
  const iso = (d) => d.toISOString().slice(0, 10);
  const ymd = (s) => { const [y, m, d] = s.slice(0, 10).split('-').map(Number); return new Date(Date.UTC(y, m - 1, d)); };
  const addMonths = (d, n) => { const r = new Date(d); const day = r.getUTCDate(); r.setUTCDate(1); r.setUTCMonth(r.getUTCMonth() + n); r.setUTCDate(Math.min(day, new Date(Date.UTC(r.getUTCFullYear(), r.getUTCMonth() + 1, 0)).getUTCDate())); return r; };
  const addDays = (d, n) => new Date(d.getTime() + n * 86400000);
  const today = ymd(new Date().toISOString());
  const monthPeriods = () => { // calendar months: latest complete month, or every month since cfg.since
    const lastEnd = addDays(new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1)), -1);
    const firstStart = cfg.since ? new Date(Date.UTC(ymd(cfg.since).getUTCFullYear(), ymd(cfg.since).getUTCMonth(), 1)) : new Date(Date.UTC(lastEnd.getUTCFullYear(), lastEnd.getUTCMonth(), 1));
    const out = [];
    for (let s = firstStart; s <= lastEnd; s = new Date(Date.UTC(s.getUTCFullYear(), s.getUTCMonth() + 1, 1))) {
      out.push({ from: iso(s), to: iso(addDays(new Date(Date.UTC(s.getUTCFullYear(), s.getUTCMonth() + 1, 1)), -1)), label: iso(s).slice(0, 7) });
    }
    return out;
  };
  const cardPeriods = (statementDate) => { // statement cycles ending on statementDate (same day each month)
    const end = ymd(statementDate);
    const out = [];
    for (let e = end, i = 0; i < 240; e = addMonths(end, -(++i))) {
      const p = { from: iso(addDays(addMonths(e, -1), 1)), to: iso(e), label: iso(e) };
      if (cfg.since ? p.to < cfg.since : i > 0) break;
      out.push(p);
    }
    return out;
  };

  // ---- accounts ------------------------------------------------------------------------------
  const LABELS = { CHEQUING: 'Chequing', SAVINGS: 'Savings', CREDIT_CARD: 'Credit card', PERSONAL_LINE_CREDIT: 'Line of credit', ISI: 'Investment', LOAN: 'Loan', MORTGAGE: 'Mortgage' };
  const accounts = (await getJson(`${API}/v2/json/accounts`)).accounts.map(a => {
    const sub = a.categorization?.subCategory;
    const label = (a.nickname || '').trim() || `${LABELS[sub] || (sub || 'Account').toLowerCase()}${a.currency && a.currency !== 'CAD' ? ` ${a.currency}` : ''}`;
    const last4 = (a.number || '').replace(/\D/g, '').slice(-4);
    return { id: a.id, label, last4, sub, currency: a.currency, status: a.status, canDownload: (a.capabilities || []).includes('DOWNLOAD_TRANSACTIONS'),
      folder: `${label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}-${last4}` };
  });

  // ---- fetchers ------------------------------------------------------------------------------
  const nativeCsv = async (acct, p) => {
    const r = await page.request.post(`${API}/v1/json/downloadTransactions`, {
      headers: { ...H, accept: 'application/vnd.api+json', 'content-type': 'application/vnd.api+json' },
      data: JSON.stringify({ downloadTransaction: { accountId: acct.id, criteria: 'DATE_RANGE', format: 'CSV', fromDate: p.from, toDate: p.to } }),
    });
    const text = await r.text();
    // 422 with problem code 0121 = no transactions in the requested range.
    if (r.status() === 422 && /"code":"0121"/.test(text)) return '';
    if (!r.ok()) throw new Error(`downloadTransactions: HTTP ${r.status()} ${text.slice(0, 200)}`);
    const fileUri = JSON.parse(text).downloadTransactions?.[0]?.fileUri;
    if (!fileUri) throw new Error(`downloadTransactions: no fileUri (${text.slice(0, 120)})`);
    // The file endpoint only works as a real browser navigation (form POST); API-style requests get HTTP 500.
    const dlP = page.waitForEvent('download', { timeout: 30000 });
    await page.evaluate(({ action, tok }) => {
      const f = document.createElement('form'); f.method = 'POST'; f.action = action;
      const i = document.createElement('input'); i.type = 'hidden'; i.name = 'X-Auth-Token'; i.value = tok;
      f.appendChild(i); document.body.appendChild(f); f.submit(); f.remove();
    }, { action: `/ebm-ai/api/v1/json/downloadTransactions/file/${fileUri}?eb-target-site=ebkpce`, tok });
    const dl = await dlP;
    // The run_code sandbox has no Buffer/TextDecoder: decode the UTF-8 bytes by hand.
    let bin = '';
    for await (const chunk of await dl.createReadStream()) for (let i = 0; i < chunk.length; i++) bin += String.fromCharCode(chunk[i]);
    await dl.delete().catch(() => {});
    return decodeURIComponent(escape(bin)).replace(/\r\n/g, '\n').trim();
  };
  const apiTransactions = async (acct, p) => {
    const all = [];
    for (let offset = 0; offset < 10000; offset += 150) {
      const params = { accountId: acct.id, filterBy: 'range', fromDate: p.from, toDate: p.to, limit: '150', offset: String(offset), sortAsc: 'true', sortByField: 'date', ...(acct.sub === 'CREDIT_CARD' ? { ccTransactionState: 'both' } : {}) };
      const q = Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&'); // no URLSearchParams in the sandbox
      const r = await page.request.get(`${API}/v1/json/transactions?${q}`, { headers: H });
      if (r.status() === 422 && offset === 0) return []; // no transactions in range
      if (!r.ok()) throw new Error(`GET transactions: HTTP ${r.status()}`);
      const b = await r.json();
      all.push(...(b.transactions || []));
      if (!b.meta?.hasNext) break;
    }
    return all;
  };

  const results = [];
  for (const acct of accounts) {
    if (!acct.canDownload) { results.push({ account: acct.label, last4: acct.last4, skipped: `no transaction download (${acct.sub})` }); continue; }
    if (acct.status !== 'ACTIVE' && !cfg.since) { results.push({ account: acct.label, last4: acct.last4, skipped: `status ${acct.status}` }); continue; }
    let periods, details = null;
    try {
      if (acct.sub === 'CREDIT_CARD') {
        details = (await getJson(`${API}/v1/json/accountDetails/${acct.id}`)).accountDetails?.details || {};
        if (!details.statementDate) throw new Error('no statementDate in accountDetails');
        periods = cardPeriods(details.statementDate);
      } else periods = monthPeriods();
    } catch (e) { results.push({ account: acct.label, last4: acct.last4, error: e.message.slice(0, 300) }); continue; }

    for (const p of periods) {
      const base = `${acct.folder}/${p.label}`;
      try {
        const body = await nativeCsv(acct, p);
        const header = acct.sub === 'CREDIT_CARD' ? 'date,description,debit,credit,card_number' : 'date,description,debit,credit';
        const rows = body ? body.split('\n').length : 0;
        await put(`${base}.csv`, `${header}\n${body ? body + '\n' : ''}`);
        const tx = await apiTransactions(acct, p).catch(async (e) => { await log(`json ${acct.last4} ${p.label}: ${e.message}`); return null; });
        await put(`${base}.json`, JSON.stringify({ account: { label: acct.label, last4: acct.last4, type: acct.sub, currency: acct.currency }, period: p,
          statement: details && acct.sub === 'CREDIT_CARD' && p.to === details.statementDate.slice(0, 10) ? details : undefined, transactions: tx }, null, 2));
        results.push({ account: acct.label, last4: acct.last4, period: `${p.from}..${p.to}`, rows, apiRows: tx ? tx.length : null, files: [`${base}.csv`, `${base}.json`],
          ...(tx && tx.filter(t => !t.pendingIndicator).length !== rows ? { warning: 'CSV row count differs from API (posted) transaction count' } : {}) });
      } catch (e) {
        await log(`error ${acct.last4} ${p.label}: ${e.message}`);
        results.push({ account: acct.label, last4: acct.last4, period: `${p.from}..${p.to}`, error: e.message.slice(0, 300) });
      }
    }
  }

  const manifest = { institution: 'cibc', generatedAt: new Date().toISOString(), mode: cfg.since ? `since ${cfg.since}` : 'latest', out: cfg.out, results };
  await put(`manifest-${iso(today)}.json`, JSON.stringify(manifest, null, 2));
  await log(`done: ${results.filter(r => r.files).length} files`);
  return { ok: !results.some(r => r.error), out: cfg.out, count: results.filter(r => r.files).length, results };
}
