# Naming a new agent

Two things get named: the **filename** (the real identity — the CLI
dedupes agents by filename minus `.agent.md`) and the **`name:`**
frontmatter field (just a display label). Get both right before you
create anything.

## Filename

- Lowercase-kebab-case, always: `thoth.agent.md`, `code-reviewer.agent.md`,
  `quartermaster.agent.md`.
- Should point at the same identity as `name:` — full or short form is
  fine (`quartermaster.agent.md` ↔ `Quartermaster`), but don't let the two
  diverge into unrelated words.

## `name:` field

- Capitalized, single word. Short, simple, memorable — something a user
  would actually type or recognize in the `/agent` picker at a glance.
- Two styles are both fine, pick whichever fits the agent's role:
  - **Functional** — the role itself, title-cased: `Quartermaster`,
    `Reviewer`. Reach for this when the role has an obvious, ready term
    and a persona would just add noise.
  - **Persona** — a recognizable reference (mythology, TV, movies) whose
    character trait maps to what the agent does: `Thoth` (Egyptian god of
    writing/wisdom) for a documentation agent. Reach for this when a
    fitting character makes the agent's purpose more memorable, not just
    decorative.
- Explore broadly for persona names — myth, television, film all fair
  game — but the reference should be genuinely recognizable and apt, not
  obscure or forced.

## Don't

- Generic placeholders: `Agent1`, `Helper`, `Assistant`.
- Trademarked or company names: no branded product/character names
  (e.g. don't name an agent after a trademarked AI assistant).
- Offensive, edgy, or in-joke names that won't read clearly to an
  outside user.

## Check for collisions before naming

Agent names are effectively repo-global (they all show up in the same
`/agent` picker), so grep before you commit to one:

```bash
# Existing filenames
find plugins .github/agents -name '*.agent.md' 2>/dev/null

# Existing display names
grep -rhoE '^name: .*' --include='*.agent.md' plugins .github/agents 2>/dev/null
```

If either the filename or the `name:` value already exists (case-insensitive),
pick a different name — don't reuse or lightly modify one that's taken.
