# waza quality bar and manifest wiring

## Scaffold with waza

`waza new skill` always drops its eval scaffold as a *sibling* of
`skills/` (e.g. `plugins/<plugin>/evals/<skill-name>/`), never inside
`skills/<skill-name>/evals/`. Discard that eval output and regenerate it
in place with `waza new eval --output` instead:

```bash
waza new skill <skill-name> --output-dir plugins/<plugin>
rm -rf plugins/<plugin>/evals/<skill-name>
cd plugins/<plugin> && waza new eval <skill-name> \
  --output skills/<skill-name>/evals/eval.yaml
```

`waza new eval` resolves `<skill-name>`'s `SKILL.md` relative to the
current directory, so it must run from the plugin root (`plugins/<plugin>`),
not the repo root. This creates
`plugins/<plugin>/skills/<skill-name>/SKILL.md` plus
`plugins/<plugin>/skills/<skill-name>/evals/{eval.yaml,tasks/}` — the
convention this repo uses. Hand-writing `SKILL.md` instead is fine too;
just still run `waza new eval ... --output` for the eval suite.

## Eval quality bar

`waza new eval`'s scaffolded grader is generic — a `relevant_content`
text grader matching `(?i)(explain|describe|analyze|implement)`. Most
workflow skills (scaffolding, renaming, wiring manifests) never emit
those words, so this grader silently fails every task while
`waza check` still reports "High compliance" (it only validates schema
shape, not that graders match real output). Always replace or remove it:

- Prefer the auto-generated `_output_contains`/`_output_not_contains`
  graders (drawn from each task's `expected.output_contains` /
  `output_not_contains`) over a blanket regex — they're precise per task.
- If you add a `text` grader, match this skill's actual expected
  vocabulary/artifacts (e.g. a created file name), not generic verbs.
- A single eval.yaml-level grader applies to *every* task, including
  negative-trigger and edge-case tasks — don't add one that only makes
  sense for the happy-path task.

Then validate, in order:

```bash
waza check plugins/<plugin>/skills/<skill-name>       # schema/compliance only
waza spec verify plugins/<plugin>/skills/<skill-name>  # tasks exercise description/USE FOR/DO NOT USE FOR
```

Finally run the eval for real (`waza check`/`spec verify` never execute
the skill). **Do this only in a sandboxed clone with no live `origin`** —
`waza run`'s `copilot-sdk` executor runs the actual Copilot CLI against
the working directory with no isolation; against this repo it can commit,
push branches, and open real PRs.

```bash
rm -rf /tmp/waza-sandbox && cp -r . /tmp/waza-sandbox
cd /tmp/waza-sandbox && git remote remove origin
waza run plugins/<plugin>/skills/<skill-name>/evals/eval.yaml
```

Confirm the run completes and no stray `copilot` process is left running
(`ps aux | grep copilot`) before deleting the sandbox.

## Compliance bar (`waza check`)

- `description`: action-verb-first sentence, 150+ characters, with a
  `USE FOR:` list and a `DO NOT USE FOR:` list.
- Routing marker: `**WORKFLOW SKILL**` right after the frontmatter.
- Body: numbered steps and code blocks (not prose paragraphs), an
  `## Example` heading with a realistic trigger prompt, and an
  error/troubleshooting heading (e.g. `## Common issues`).
- Token budget: keep `SKILL.md` itself under ~500 tokens; move detailed
  templates, examples, and command listings into a linked
  `references/*.md` file instead of inlining everything.

Run and fix:

```bash
waza check plugins/<plugin>/skills/<skill-name>
```

## Wiring into the plugin

Confirm `plugin.json`'s `skills` field covers the new directory. The
default bare `skills/` (or an omitted field) covers it automatically; if
`skills` lists explicit paths, add the new one.

## Reinstall and verify

```bash
copilot plugin install ./plugins/<plugin>
```

In an interactive session, run `/skills list`, then invoke the skill.
