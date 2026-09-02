# How to update an installed agentry plugin

## Preconditions

- GitHub Copilot CLI is installed and you can run `copilot` on your
  harness.
- The plugin (`general`, `engineer`, or `writing`) is already installed —
  see [install-agentry-plugin.md](install-agentry-plugin.md) if it isn't.
- The `agentry` marketplace is still registered
  (`copilot plugin marketplace list` shows it).

## 1. Refresh the marketplace source

`copilot plugin update` reads from the marketplace source you registered,
so make sure that source is current first.

**Installed from the published repo:** re-add the marketplace to refresh
the CLI's copy of it.

```bash
copilot plugin marketplace add ani1797/agentry
```

**Installed from a local clone:** pull the latest changes into that
clone instead — the CLI reads the marketplace straight from the path you
registered.

```bash
cd /path/to/agentry
git pull
```

## 2. Update the plugin

```bash
copilot plugin update PLUGIN-NAME
```

Swap `PLUGIN-NAME` for `general`, `engineer`, or `writing`. To update
every installed plugin at once:

```bash
copilot plugin update --all
```

## 3. Verify

```bash
copilot plugin list
```

Confirm the version now matches the marketplace entry
(`.github/plugin/marketplace.json` if you're tracking a local clone). In
an interactive `copilot` session, also check:

```
/agent
/skills list
```

Both should reflect any agents/skills added, changed, or removed by the
update.

## Done looks like

- `copilot plugin list` shows the new version for the plugin you updated.
- `/agent` / `/skills list` reflect the updated set of components.

## Troubleshooting

- **Version unchanged after update:** re-run step 1 — the CLI updates
  from its registered marketplace snapshot, so a stale marketplace source
  (not re-added, or an unpulled local clone) is the usual cause.
- **`copilot plugin update` reports "not found":** confirm the plugin
  name matches exactly what `copilot plugin list` shows; it's the
  `name` field from `plugin.json`, not the directory path.
- **Components missing after update:** re-run `/skills list` /  `/agent`
  in a fresh session — the CLI cache can lag behind an update within an
  already-open session.

## Related tasks

- Install the plugin for the first time:
  [install-agentry-plugin.md](install-agentry-plugin.md).
- Remove the plugin: `copilot plugin uninstall PLUGIN-NAME`.
- Contributing an update to a plugin's content yourself (not just
  consuming one): use the `scaffold-skill`, `scaffold-agent`, or
  `multi-primitive-update` skill depending on scope.
