// Wealthsimple login. Run via browser_run_code_unsafe { filename: <scripts.login> }.
// Returns {status: "logged_in" | "needs_user", step, detail}. Never returns secrets.
async (page) => {
  const BRIDGE = '__BRIDGE_URL__';
  const bridge = async (p) => {
    const r = await page.request.get(`${BRIDGE}/${p}`).catch(() => null);
    return r && r.ok() ? (await r.text()).trim() : null;
  };
  const loggedIn = () => /\/app\/(home|docs|account|trade|cash)/.test(page.url());
  const visible = (loc) => loc.first().isVisible().catch(() => false);

  if (!page.url().startsWith('https://my.wealthsimple.com/app')) {
    await page.goto('https://my.wealthsimple.com/app/login');
  }
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(2000);
  if (loggedIn()) return { status: 'logged_in', step: 'already' };

  const cfg = JSON.parse((await bridge('config')) || '{}');
  if (!cfg.has_credentials) return { status: 'needs_user', step: 'credentials', detail: 'No stored credentials; ask the user to sign in in the browser window.' };

  const email = page.getByRole('textbox', { name: 'Email' });
  if (await visible(email)) {
    const u = await bridge('secret/username');
    const p = await bridge('secret/password');
    if (!u || !p) return { status: 'needs_user', step: 'credentials', detail: 'username/password not available from bridge' };
    await email.fill(u);
    await page.getByRole('textbox', { name: 'Password' }).fill(p);
    await page.getByRole('button', { name: 'Log in', exact: true }).click();
  }

  // Walk through second-factor screens for up to ~45s.
  const deadline = Date.now() + 45000;
  let otpTries = 0;
  while (Date.now() < deadline) {
    await page.waitForTimeout(1500);
    if (loggedIn()) return { status: 'logged_in', step: 'done' };

    const code = page.getByRole('textbox', { name: /code/i });
    // Passkey challenge: switch to the authenticator (TOTP) method.
    if (!(await visible(code)) && await visible(page.getByRole('heading', { name: /passkey/i }))) {
      await page.getByRole('button', { name: /try another way/i }).first().click();
      continue;
    }
    // Landed on the "choose another way" list by mistake: go back to the default method.
    if (await visible(page.getByRole('heading', { name: /choose another way/i }))) {
      await page.getByRole('button', { name: 'Back' }).click();
      continue;
    }
    if (await visible(code)) {
      if (!cfg.has_otp || otpTries >= 2) {
        return { status: 'needs_user', step: '2fa', detail: 'Verification code required (SMS/email or TOTP failed). Ask the user to complete it in the browser.' };
      }
      otpTries++;
      const otp = await bridge('otp');
      if (!otp) return { status: 'needs_user', step: '2fa', detail: 'Verification code not available from 1Password; ask the user to enter it in the browser.' };
      await code.first().fill(otp);
      const submit = page.getByRole('button', { name: /submit|verify|continue/i });
      // The form usually auto-submits after 6 digits; click only if still enabled.
      await page.waitForTimeout(1000);
      if (await visible(submit) && await submit.first().isEnabled().catch(() => false)) await submit.first().click().catch(() => {});
      await page.waitForTimeout(3000);
      continue;
    }

    const err = page.getByRole('alert');
    if (await visible(err)) return { status: 'needs_user', step: 'error', detail: (await err.first().innerText()).slice(0, 200) };
  }
  return { status: loggedIn() ? 'logged_in' : 'needs_user', step: 'timeout', detail: page.url() };
}
