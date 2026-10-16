// CIBC Online Banking login. Run via the bridge loader (`run.login`).
// Returns {status: "logged_in" | "needs_user", step, detail}. Never returns secrets.
async (page) => {
  const BRIDGE = '__BRIDGE_URL__';
  const SIGNON = 'https://www.cibconline.cibc.com/ebm-resources/online-banking/client/index.html#/auth/signon';
  const bridge = async (p) => { const r = await page.request.get(`${BRIDGE}/${p}`).catch(() => null); return r && r.ok() ? (await r.text()).trim() : null; };
  const visible = (loc) => loc.first().isVisible().catch(() => false);
  const hasToken = () => page.evaluate(() => !!sessionStorage.getItem('ebanking:session_token')).catch(() => false);
  const loggedIn = async () => /cibconline\.cibc\.com\/ebm-resources\/(online-banking\/accounts|public\/banking)/.test(page.url()) && await hasToken();

  if (await loggedIn()) return { status: 'logged_in', step: 'already' };
  if (!/^https:\/\/(secure\.cibc\.com|www\.cibconline\.cibc\.com)\//.test(page.url())) { await page.goto(SIGNON); }
  await page.waitForTimeout(3000);
  if (await loggedIn()) return { status: 'logged_in', step: 'already' };

  const cfg = JSON.parse((await bridge('config')) || '{}');
  let username = null, passwordUsed = false, cardStepDone = false;
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    if (await loggedIn()) return { status: 'logged_in', step: 'done' };

    const cookies = page.getByRole('button', { name: /accept all cookies/i });
    if (await visible(cookies)) { await cookies.first().click().catch(() => {}); continue; }

    // Post-sign-on interstitials (offers, surveys, profile reminders)
    const skip = page.getByRole('button', { name: /^(remind me later|no thanks|not now|skip|maybe later|continue to (my )?accounts)/i });
    if (await visible(skip)) { await skip.first().click().catch(() => {}); await page.waitForTimeout(2500); continue; }

    // One-time verification code (SMS/email/app): only the user can complete this.
    if (await visible(page.getByText(/verification code|one-time|OTVC|verify your identity/i))) {
      return { status: 'needs_user', step: '2fa', detail: 'CIBC is asking for a one-time verification code. Ask the user to complete it in the browser, then re-run login.' };
    }

    const pwd = page.getByRole('textbox', { name: /password/i });
    if (await visible(pwd)) {
      if (passwordUsed) { await page.waitForTimeout(2000); if (await visible(page.getByRole('alert'))) return { status: 'needs_user', step: 'password', detail: (await page.getByRole('alert').first().innerText()).slice(0, 200) }; continue; }
      if (!cfg.has_credentials) return { status: 'needs_user', step: 'credentials', detail: 'No stored credentials; ask the user to sign in in the browser window.' };
      const p = await bridge('secret/password');
      if (!p) return { status: 'needs_user', step: 'credentials', detail: 'password not available from bridge (restart bridge?)' };
      await pwd.first().fill(p);
      passwordUsed = true;
      await page.getByRole('button', { name: /^sign on$/i }).first().click();
      await page.waitForTimeout(5000);
      continue;
    }

    // Card step: either a remembered-card list (checkbox per card) or a card-number textbox.
    const cardBox = page.getByRole('textbox', { name: /card number/i });
    if (!cardStepDone && (await visible(cardBox) || await visible(page.getByRole('heading', { name: /sign on to cibc/i })))) {
      if (!cfg.has_credentials) return { status: 'needs_user', step: 'credentials', detail: 'No stored credentials; ask the user to sign in in the browser window.' };
      username = username || (await bridge('secret/username')) || '';
      const digits = username.replace(/\D/g, '');
      const last4 = digits.slice(-4);
      if (!(await visible(cardBox))) {
        const labels = await page.getByRole('checkbox').evaluateAll(cs => cs.map(c => c.getAttribute('aria-label') || c.closest('label, li')?.textContent || ''));
        const idx = labels.findIndex(l => l.replace(/\s/g, '').endsWith(last4) || l.includes(last4));
        if (idx >= 0) {
          const cb = page.getByRole('checkbox').nth(idx);
          if (!(await cb.isChecked().catch(() => false))) await cb.check().catch(() => {});
        } else {
          await page.getByRole('button', { name: /different card/i }).first().click();
          await page.waitForTimeout(1500);
        }
      }
      if (await visible(cardBox)) await cardBox.first().fill(digits);
      cardStepDone = true;
      await page.getByRole('button', { name: /^continue$/i }).first().click();
      await page.waitForTimeout(3000);
      continue;
    }
    await page.waitForTimeout(1500);
  }
  return { status: (await loggedIn()) ? 'logged_in' : 'needs_user', step: 'timeout', detail: page.url().split('?')[0] };
}
