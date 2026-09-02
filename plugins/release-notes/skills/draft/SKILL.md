---
name: draft
description: >
  Draft release notes from merged pull requests in a GitHub repository.
  Fetches PRs merged since the last tag (or a specified range), groups
  changes by label/type, and produces a structured Markdown draft ready
  for review. USE FOR: generating a first-draft changelog or release
  announcement from merged PR titles and descriptions. DO NOT USE FOR:
  publishing or tagging a release, writing commit-message summaries, or
  summarising open/unmerged PRs.
---

**WORKFLOW SKILL**

# Draft release notes from merged PRs

## Overview

Fetches merged PRs from a GitHub repository for a given version range,
groups them by change type, and writes a structured Markdown draft.

## Steps

1. Determine the repo and range: use `--repo owner/repo` and
   `--since-tag <tag>` (or `--base`/`--head` SHAs). Fall back to the
   authenticated repo if not specified.
2. Fetch merged PRs with `gh pr list --state merged --search "merged:>DATE"`.
3. Group PRs by label: `feat`→Features, `fix`→Bug Fixes,
   `chore`/`deps`→Maintenance, unlabelled→Other Changes.
4. Render the Markdown draft:
   ```
   ## <version> — <date>
   ### Features
   - <PR title> (#<number>)
   ### Bug Fixes
   - ...
   ```
5. Write the draft to `CHANGELOG.md` (or print to stdout if `--dry-run`).

## Example

> "Draft release notes for v1.3.0 from PRs merged since v1.2.0."

Run the skill; it fetches PRs merged after the `v1.2.0` tag, groups
them, and outputs a Markdown draft under `## v1.3.0`.

## Common issues

- No PRs found: verify the tag exists (`gh release list`) and the date
  range covers the expected window.
- Labels missing: unlabelled PRs land in "Other Changes" — triage labels
  before drafting or edit the output manually.
- Auth error: ensure `gh auth status` shows a valid token with `repo`
  scope.
