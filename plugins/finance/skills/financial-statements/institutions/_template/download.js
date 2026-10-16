// Template downloader. Prefer replaying the portal's own JSON/CSV endpoints with the session.
async (page) => {
  const BRIDGE = '__BRIDGE_URL__';
  const cfg = await (await page.request.get(`${BRIDGE}/config`)).json();
  const put = async (path, content) => {
    const r = await page.request.put(`${BRIDGE}/file?path=${encodeURIComponent(path)}`, { data: content });
    if (!r.ok()) throw new Error(`bridge write failed ${path}: ${r.status()}`);
  };
  const csv = (header, rows) => [header, ...rows].map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n') + '\n';

  // TODO 1: list accounts -> [{ id, label, currency }]
  const accounts = [];
  const results = [];
  for (const a of accounts) {
    try {
      // TODO 2: find latest statement period (or every period >= cfg.since) for account a
      // TODO 3: fetch transactions (API) or click the portal's CSV/OFX button and capture the download
      const period = 'YYYY-MM';
      const rows = [];
      const folder = `${a.label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}__${a.id}`;
      await put(`${folder}/${period}.csv`, csv(['date', 'description', 'amount', 'balance', 'currency'], rows));
      results.push({ account: a.label, accountId: a.id, period, rows: rows.length, files: [`${folder}/${period}.csv`] });
    } catch (e) {
      results.push({ account: a.label, accountId: a.id, error: String(e.message).slice(0, 300) });
    }
  }
  await put(`manifest-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify({ generatedAt: new Date().toISOString(), results }, null, 2));
  return { ok: !results.some(r => r.error), out: cfg.out, count: results.length, results };
}
