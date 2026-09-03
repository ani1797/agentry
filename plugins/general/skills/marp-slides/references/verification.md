# Visual verification

Marp is a browser-rendered format — always visually check slides before
exporting final output. Do this in a scratch directory, not in
`docs/slides/NAME/output/`, so `output/` only ever holds the final
`NAME.pdf` / `NAME.pptx` / `NAME.html`.

## Render preview images

```bash
tmp=$(mktemp -d)
marp docs/slides/NAME/main.md --images png -o "$tmp/slide.png" --allow-local-files
ls "$tmp"   # slide.001.png, slide.002.png, ...
```

Use the `view` tool to open every `slide.NNN.png` in `$tmp` (images are a
supported input to `view`). Review each one against this checklist:

- **Overflow/clipping** — text or images cut off at slide edges or
  bottom; especially wide code blocks, long bullet lists, big headings.
- **Contrast/readability** — text color vs. background color (check
  `invert`/dark slides and any custom `backgroundColor`/`style` tweaks).
- **Layout correctness** — split (`bg left`/`bg right`) and multi-`bg`
  slides show images in the intended position/size; no distortion.
- **Icons/images** — emoji or `assets/` images actually rendered, not
  broken/missing (a missing local asset shows as a blank box).
- **Theme consistency** — `lead`/title slides centered as expected;
  headers/footers/pagination appear where intended across slides.
- **Content density** — one idea per slide; no wall-of-text slide.

## Fix and re-check

For every issue found, edit `main.md` (adjust directive, split slide,
resize image, tweak `style`), delete the old `$tmp`, and re-render with a
fresh `mktemp -d`. Repeat until a full pass finds no issues — do not
proceed to export while any slide still has a visible defect.

## Clean up

```bash
rm -rf "$tmp"
```

Preview PNGs are scratch artifacts only; never leave them under
`docs/slides/NAME/` or commit them.
