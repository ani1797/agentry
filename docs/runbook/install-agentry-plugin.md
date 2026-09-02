# How to install an agentry plugin on your Copilot CLI harness

## Preconditions

- GitHub Copilot CLI is installed and you can run `copilot` on your harness.
- You know which plugin you want (`general`, `engineer`, or `writing`), or
  you're installing from a local clone of this repo for development.
- For a remote install, you have network access to this repository
  (`ani1797/agentry`).

## 1. Register the marketplace

Pick one, depending on where you're working from.

**From a local clone (development):**

```bash
cd /path/to/agentry
copilot plugin marketplace add .
```

**From the published repo (no local clone needed):**

```bash
copilot plugin marketplace add ani1797/agentry
```

This registers `agentry` as a marketplace source; it does not install any
plugin yet.

## 2. Install a plugin

**By marketplace reference** (works after step 1, either form):

```bash
copilot plugin install writing@agentry
```

Swap `writing` for `general` or `engineer` to install a different plugin.

**By local path directly** (skips needing the plugin already registered,
useful when iterating on an unpublished change):

```bash
copilot plugin install ./plugins/writing
```

## 3. Verify

```bash
copilot plugin list
```

Confirm the plugin appears with the expected version. In an interactive
`copilot` session, also check:

```
/agent
/skills list
```

Both should list the agents and skills shipped by the plugin you installed
(e.g. `writing` ships the `thoth` agent and the `diataxis` skill).

## Done looks like

- `copilot plugin list` shows the plugin, and `/agent` / `/skills list`
  surface its components in an interactive session.

## Troubleshooting

- **Plugin missing after install:** re-run
  `copilot plugin install ./plugins/<name>` (or the `@agentry` form) — the
  CLI cache can go stale after manifest edits.
- **Marketplace not found:** confirm `.github/plugin/marketplace.json`
  exists at the repo root you pointed at; the CLI resolves it from
  `marketplace.json`, `.plugin/marketplace.json`,
  `.github/plugin/marketplace.json`, or `.claude-plugin/marketplace.json`,
  in that order.

## Related tasks

- Update the plugin: `copilot plugin update PLUGIN-NAME`
- Remove the plugin: `copilot plugin uninstall PLUGIN-NAME`
- Remove the marketplace: `copilot plugin marketplace remove agentry`
  (add `--force` if plugins from it are still installed)
