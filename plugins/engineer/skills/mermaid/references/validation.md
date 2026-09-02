# Validating diagrams with mmdc

`mmdc` (from `@mermaid-js/mermaid-cli`) renders a diagram; a non-zero exit
code or stderr output means the syntax is invalid. Use it as the validator
for every diagram before it's considered done — a diagram that fails to
render is a bug, not a style issue.

## Standalone `.mmd` files (`docs/diagrams/*.mmd`)

The rendered image is a committed artifact, so render it in place:

```bash
mmdc -i docs/diagrams/auth-flow.mmd -o docs/diagrams/auth-flow.svg -q -t neutral -b transparent
echo "exit: $?"
```

Re-run this any time `auth-flow.mmd` changes, so the checked-in `.svg`
never drifts from its source. Reference it from markdown:

```md
![Auth request flow](../diagrams/auth-flow.svg "Auth request flow")
```

## Embedded fenced blocks in markdown

Two options, in order of preference:

**A. Validate the whole file in one pass** (fastest, checks every block):

```bash
tmp_dir=$(mktemp -d)
mmdc -i path/to/doc.md -o "$tmp_dir/preview.md" -a "$tmp_dir" -q
echo "exit: $?"      # non-zero => at least one embedded diagram is broken
rm -rf "$tmp_dir"
```

This rewrites `preview.md` with each fenced block swapped for an `<img>` —
discard it, the goal is only the exit code / stderr from parsing.

**B. Validate one block in isolation** (when you need to know exactly which
block failed): copy the fenced block's contents (excluding the ` ```mermaid `
fence lines) into a temp `.mmd` and render it:

```bash
tmp=$(mktemp --suffix=.mmd)
cat > "$tmp" <<'EOF'
sequenceDiagram
    Client->>Auth: request token
    Auth-->>Client: token
EOF
mmdc -i "$tmp" -o "${tmp%.mmd}.svg" -q
echo "exit: $?"
rm -f "$tmp" "${tmp%.mmd}.svg"
```

## Reading errors

`mmdc` stderr reports a parse error with a line number counted from the
start of the diagram body (line 1 = the diagram's start keyword, e.g.
`flowchart TD`), not from the markdown file. Fix the reported line, then
re-run the same command until it exits 0.

## Useful flags

- `-t neutral` — theme that reads well on both light and dark GitHub themes.
- `-b transparent` — transparent background for SVG embeds.
- `-q` — suppress non-error log noise so exit code / stderr is the signal.
- `-c mermaidConfig.json` — pass shared config (e.g. `theme`, `flowchart.curve`)
  when several diagrams in a repo need consistent rendering options.

## Setup

`mmdc` is the CLI from `@mermaid-js/mermaid-cli`:

```bash
npm install -g @mermaid-js/mermaid-cli   # or: npx -p @mermaid-js/mermaid-cli mmdc
mmdc --version
```

## Sandboxed / CI environments

`mmdc` launches headless Chromium via Puppeteer. In containers without a
working sandbox you may see a Chromium sandbox error. Fix with a puppeteer
config that disables the sandbox:

```bash
echo '{"args": ["--no-sandbox"]}' > /tmp/puppeteer-config.json
mmdc -p /tmp/puppeteer-config.json -i docs/diagrams/auth-flow.mmd -o docs/diagrams/auth-flow.svg
```

See the upstream
[Linux sandbox issue doc](https://github.com/mermaid-js/mermaid-cli/blob/master/docs/linux-sandbox-issue.md)
before disabling the sandbox in any shared/untrusted environment.
