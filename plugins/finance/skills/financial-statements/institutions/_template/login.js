// Template login: fill selectors for the portal. Returns {status, step, detail}; never returns secrets.
async (page) => {
  const BRIDGE = '__BRIDGE_URL__';
  const bridge = async (p) => { const r = await page.request.get(`${BRIDGE}/${p}`).catch(() => null); return r && r.ok() ? (await r.text()).trim() : null; };
  const loggedIn = () => /\/dashboard|\/accounts/.test(page.url()); // TODO
  if (loggedIn()) return { status: 'logged_in', step: 'already' };

  const cfg = JSON.parse((await bridge('config')) || '{}');
  if (!cfg.has_credentials) return { status: 'needs_user', step: 'credentials', detail: 'Ask the user to log in in the browser window.' };

  await page.getByLabel(/user|email|card/i).first().fill(await bridge('secret/username') || ''); // TODO
  await page.getByLabel(/password/i).first().fill(await bridge('secret/password') || '');        // TODO
  await page.getByRole('button', { name: /sign in|log in/i }).first().click();                 // TODO

  for (let i = 0; i < 20 && !loggedIn(); i++) {
    await page.waitForTimeout(1500);
    const code = page.getByRole('textbox', { name: /code/i });
    if (await code.first().isVisible().catch(() => false)) {
      if (!cfg.has_otp) return { status: 'needs_user', step: '2fa', detail: 'Enter the verification code in the browser.' };
      const otp = await bridge('otp');
      if (!otp) return { status: 'needs_user', step: '2fa', detail: 'Enter the verification code in the browser.' };
      await code.first().fill(otp);
      await page.keyboard.press('Enter');
    }
  }
  return loggedIn() ? { status: 'logged_in', step: 'done' } : { status: 'needs_user', step: 'timeout', detail: page.url() };
}
