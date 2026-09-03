# Marp / Marpit reference

Full docs: https://marp.app/ (product overview) and
https://marpit.marp.app/ (Markdown framework spec). This is a condensed
cheat-sheet for authoring `docs/slides/NAME/main.md`.

## Front matter (required for VS Code live preview)

```yaml
---
marp: true            # activates Marp mode — must be present and first
theme: default         # default | gaia | uncover (built-in), or a custom theme name
paginate: true         # true | false | hold | skip
size: 16:9             # 16:9 (1280x720, default) or 4:3 (960x720)
title: My Deck
author: Jane Doe
description: One-line summary
headingDivider: 2      # optional: auto-split slides at headings >= level 2
---
```

## Slide separation

Slides split on a line containing only `---` (after front matter). Prefer
one topic/idea per slide; keep bullet lists short (≤6 lines) so content
never overflows.

## Directives (global vs. local vs. spot)

Set as an HTML comment `<!-- key: value -->` or in front matter.
**Global** directives (`theme`, `size`, `style`, `headingDivider`, `lang`)
apply to the whole deck. **Local** directives (`paginate`, `header`,
`footer`, `class`, `backgroundColor`, `backgroundImage`, `color`, etc.)
apply from the defining slide onward. Prefix with `_` (e.g. `_class`) to
apply a **spot** directive to only the current slide.

```markdown
<!-- _class: lead -->
# Title Slide
## Subtitle

---

<!-- header: 'My Deck' -->
<!-- footer: '© 2026' -->
## A content slide
```

### Useful classes from built-in themes

- `lead` — centers content, good for title/section slides.
- `invert` — swaps background/foreground colors (dark slide).

### Tweaking theme CSS inline

```markdown
---
theme: default
style: |
  section { font-size: 28px; }
  h1 { color: #0288d1; }
---
```

## Layout via images and backgrounds

Extended image syntax packs layout keywords into the alt text:

```markdown
![bg](assets/photo.jpg)              # full-slide background (cover)
![bg contain](assets/photo.jpg)      # fit without cropping
![bg left](assets/photo.jpg)         # split layout: image left, content right
![bg left:33%](assets/photo.jpg)     # custom split size
![bg right vertical](assets/a.png)
![bg](assets/b.png)                  # multiple stacked backgrounds
![w:200 h:150](assets/icon.png)      # inline image, explicit size
![blur:5px opacity:.8](assets/x.png) # CSS filters on inline/advanced bg images
```

Put all local images (photos, diagrams, icons) under
`docs/slides/NAME/assets/` and reference them with relative paths.

## Icons

Marp has no dedicated icon directive; use one of:
1. **Emoji shortcodes/Unicode** (`:rocket:`, 🚀) — rendered as crisp
   Twemoji SVGs by Marp Core, zero assets needed. Best default for icons.
2. **SVG/PNG assets** under `assets/` sized with `![w:32 h:32](...)`.

## Fit / auto-scaling

```markdown
# <!-- fit --> A Big Fitting Headline
```

Scales the heading to the slide width. Built-in themes also auto-shrink
wide code blocks.

## Speaker notes

Any HTML comment that isn't a recognized directive is a presenter note,
hidden from rendered output but exported with `--pdf-notes` or `--notes`:

```markdown
## Slide with notes

<!-- Remember to mention the Q3 roadmap here. -->
```

## Built-in themes

`default`, `gaia`, `uncover` — set via `theme:`. Combine with `_class: lead`
/ `_class: invert` local classes for title and dark slides. Custom themes
are possible via `--theme` (marp CLI) pointing at a CSS file, but built-in
themes cover most quick-deck needs.

## Exporting (marp CLI)

```bash
marp docs/slides/NAME/main.md -o docs/slides/NAME/output/NAME.pdf --allow-local-files
marp docs/slides/NAME/main.md -o docs/slides/NAME/output/NAME.pptx --allow-local-files
marp docs/slides/NAME/main.md -o docs/slides/NAME/output/NAME.html --allow-local-files
```

- `--allow-local-files` is required for PDF/PPTX/image conversion whenever
  the deck references local `assets/` files (browser-based rendering
  blocks local files by default).
- `--pdf-notes` embeds presenter notes as PDF annotations.
- `--pptx-editable` (experimental, needs LibreOffice too) produces an
  editable PPTX instead of pre-rendered slide images.
- Add `-w`/`--watch` while iterating locally to auto-reconvert on save.
