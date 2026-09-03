# Getting started with the marp CLI

The `marp-slides` skill shells out to the `marp` command to export decks to
PDF, PPTX, and HTML. If it isn't installed:

```bash
# One-shot, no install (requires Node.js 18+)
npx @marp-team/marp-cli@latest docs/slides/NAME/main.md -o docs/slides/NAME/output/NAME.pdf

# Or install into the repo
npm install --save-dev @marp-team/marp-cli

# Or install globally
npm install -g @marp-team/marp-cli

# Or via package manager
brew install marp-cli   # macOS/Linux
scoop install marp       # Windows
```

PDF, PPTX, and image export additionally require a local browser — Google
Chrome, Microsoft Edge, or Mozilla Firefox. HTML export has no browser
requirement.

Full CLI reference: https://github.com/marp-team/marp-cli
