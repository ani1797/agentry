# Multi-plugin change checklist

## 1. Enumerate before editing

List every `plugin.json`, the `marketplace.json` entry, every `SKILL.md`,
and every `agent.md` the change must touch. Don't discover missing files
mid-edit.

## 2. Edit as one atomic unit per plugin

If a rename is involved, move directories with `git mv` so history follows
the file, then update paths inside the moved manifests.

## 3. Keep duplicated metadata in sync

`plugin.json` `name`/`version`/`description` must match the
`marketplace.json` entry for that plugin at every commit that touches
either file — for every plugin in scope, not just the first.

## 4. Validate every touched file

```bash
jq -e . .github/plugin/marketplace.json > /dev/null
for p in plugins/<name1>/plugin.json plugins/<name2>/plugin.json; do
  jq -e . "$p" > /dev/null || echo "invalid JSON: $p"
done
waza check plugins/<name1>/skills/<skill> plugins/<name2>/skills/<skill>
```

`waza check` only validates schema/compliance, not that a skill's evals
actually pass — it will report "High compliance" even if every grader
silently fails (e.g. the scaffolded `relevant_content` regex grader,
which rarely matches non-explain/analyze workflow output). For any
touched skill with an eval suite, also run `waza spec verify` and a
sandboxed `waza run` (see scaffold-skill's `references/waza-and-manifest.md` "Eval quality
bar" section for the grader-tailoring and sandboxing steps —
`waza run`'s executor is not sandboxed and can commit/push for real).

## 5. Reinstall and re-verify

Reinstall every touched plugin locally and re-verify with `/agent` /
`/skills list` before opening the PR.

## 6. Scope the PR

One PR per logical change. Bundle primitives together only when
introduced, renamed, or removed atomically as a single unit — don't fold
in unrelated drive-by edits to other plugins.

## 7. Describe scope in the PR

Enumerate every primitive touched — plugin, skill, or agent name plus
path — so a reviewer can check each one individually.
