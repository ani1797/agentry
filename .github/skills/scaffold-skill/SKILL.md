---
name: scaffold-skill
description: >
  Scaffold a new workflow skill inside an existing agentry plugin, from
  SKILL.md frontmatter through the waza quality bar and eval suite. USE
  FOR: adding a workflow-oriented skill to a plugin that already exists and
  meeting waza check's compliance bar. DO NOT USE FOR: creating a
  brand-new plugin (scaffold-plugin) or a specialist agent role
  (scaffold-agent).
---

**WORKFLOW SKILL**

# Scaffold a new skill

## Overview

A skill is one workflow within a plugin, invocable as a slash command
with its own `SKILL.md`. This scaffolds it to the `waza check`
compliance bar and — just as importantly — proves the skill and its
eval suite actually work by running them for real, not just passing
schema checks. Pick the plugin by business function; don't create one
for a single skill.

## Steps

1. Pick the plugin the skill belongs to (use `scaffold-plugin` first if
   none fits).
2. Scaffold `SKILL.md` + eval so it lands at `skills/<name>/evals/` (not
   `waza new skill`'s sibling default) — commands in
   [references/waza-and-manifest.md](references/waza-and-manifest.md).
3. Write frontmatter/body for `waza check`; confirm `plugin.json`'s
   `skills` field covers the new directory.
4. Write real tasks/graders: a happy path, an edge case, and a
   negative/boundary task targeting this skill's own `DO NOT USE FOR`
   list (not just an unrelated prompt). Replace the scaffolded
   boilerplate grader with one tied to real trigger vocabulary and
   output — reference doc's "eval quality bar" covers grader types and
   pitfalls.
5. Validate in order: `waza check` (schema only), `waza spec verify`
   (confirms tasks exercise description/USE FOR/DO NOT USE FOR — `check`
   doesn't), then `waza run` in a sandboxed clone with no live `origin`.
   `waza check` passing alone doesn't prove the skill works.
6. Reinstall, verify with `/skills list`, invoke the skill.

## Example

> "Add a `draft` skill to `release-notes` that drafts notes from merged
> PRs."

Scaffold per the reference doc, write tasks for the happy path, an edge
case, and the DO NOT USE FOR boundary, tailor the grader, run
check → spec-verify → sandboxed-run, reinstall, verify.

## Common issues

- Low compliance: missing `USE FOR:`/`DO NOT USE FOR:`, short
  description, or prose instead of numbered steps.
- Eval in `plugins/<plugin>/evals/<name>/`: `waza new skill`'s default;
  delete, regenerate per reference doc.
- `waza check` passes but `waza run` fails: the scaffolded
  `relevant_content` grader rarely matches real output — tailor or
  remove it (reference doc).
- `waza spec verify` shows uncovered `DO NOT USE FOR`: add a task with a
  `skill_invocation` grader's `forbidden_skills` (reference doc example).
- Missing after reinstall: rerun `copilot plugin install ./plugins/<plugin>`.
