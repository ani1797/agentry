# Agent frontmatter template and validation

```markdown
---
name: <Name>
description: One sentence describing what the agent does and when to use it.
tools:
  - read
  - edit
  - search
---

# <Name>

You are ...
```

`name` and `description` are required. Add `tools`, `model`,
`disable-model-invocation`, `user-invocable`, `mcp-servers`, or `metadata`
only if the agent actually needs them — don't grant tools it won't use. Do
not add a `skills:` field: skills load on demand via the `skill` tool,
never preloaded into an agent.

## Validate the frontmatter

```bash
python3 -c "
import re, yaml
text = open('plugins/<plugin>/agents/<name>.agent.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
yaml.safe_load(m.group(1))
"
```

## Reinstall and verify

```bash
copilot plugin install ./plugins/<plugin>
```

In an interactive session, run `/agent` to confirm it's listed, then invoke
it to sanity check tool access and behavior.
