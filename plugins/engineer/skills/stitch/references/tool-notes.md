# Stitch tool notes

Verified by hands-on exploration of the Stitch MCP server.

## Ids: screen vs. screen instance

`get_project` returns `screenInstances`, each with its own `id` (e.g.
`c5355a41d7d94d0b8dbf3f16fc651e13`) and a `sourceScreen` field pointing
at `projects/{project}/screens/{screen}`. For most single-project
workflows the instance id and screen id are the same string, but
`apply_design_system`'s `selectedScreenInstances` explicitly wants both
the instance `id` *and* its `sourceScreen` resource name — always read
both off `get_project`, don't assume one from the other, and never
substitute a raw `screens/...` id where an instance is expected.

## Design system lifecycle

`create_design_system` returns an `assets/{id}` resource but does not
by itself make the system visible/active in the UI or default screen
generation — always immediately follow with `update_design_system`
(same theme payload, plus the returned `name`). This pairing is called
out in both tools' own descriptions; skipping the second call is the
most common way a "created" theme silently doesn't apply.

Multiple design systems can coexist per project (`list_design_systems`
returns an array). Use this for:
- Multi-brand or multi-product prototypes in one project.
- Light/dark or seasonal theme variants of the same screens — generate
  or re-skin a duplicate screen set per theme via `apply_design_system`.

`list_design_systems` with no `projectId` lists *global* design system
assets (reusable across projects); pass `projectId` to scope to one
project's systems.

## Screen generation vs. editing vs. variants

| Goal | Tool | Behavior observed |
|---|---|---|
| New screen/flow step | `generate_screen_from_text` | Full generation; may also emit supporting image assets (e.g. an illustration) alongside the real HTML screen. Returns `outputComponents` — surface any `text` and `suggestion` entries to the user. |
| Targeted tweak | `edit_screens` | Scoped DOM operations (`replace_content`, `insert_after`, selector-targeted) verified against the current HTML — confirmed to leave unrelated markup untouched. Also returns follow-up `suggestion` entries. |
| Alternatives to compare | `generate_variants` | `variantOptions.aspects` restricts what changes (`LAYOUT`, `COLOR_SCHEME`, `IMAGES`, `TEXT_FONT`, `TEXT_CONTENT`); `creativeRange` controls how far from the original (`REFINE` < `EXPLORE` < `REIMAGINE`, default `EXPLORE`); `variantCount` 1-5. |
| Re-skin many screens at once | `apply_design_system` | Applies one design system's tokens to a list of screen instances in one call — the only tool that fans a single change out to many screens. |

`generate_screen_from_text`, `edit_screens`, and `generate_variants` can
take a couple of minutes; per each tool's own description, do not retry
on timeout — poll `get_screen` instead.

## Verifying real output

`get_screen`'s `htmlCode.downloadUrl` is real Tailwind-class HTML tied to
the design system's token names (`bg-primary`, `text-on-primary`, etc.),
not a static mock. To validate interaction/responsiveness beyond the
screenshot:
1. Fetch/save the HTML from `downloadUrl`.
2. `playwright-browser_navigate` to the local file, `browser_snapshot`
   for the accessibility tree (actions), `browser_take_screenshot` for
   visual diffing across variants.

Use `context7-resolve-library-id` + `context7-query-docs` before
hand-editing generated markup to confirm you're using the same
utility-class conventions (e.g. Tailwind) the generator already used,
rather than introducing a second styling approach.

## DESIGN.md import path

`upload_design_md` → `create_design_system_from_design_md` lets an
existing brand/style spec seed a design system directly instead of
building one field-by-field with `create_design_system`. Requires an
existing screen instance to anchor the extraction (`selectedScreenInstance`),
so run this after at least one screen or the design-system-instance
placeholder exists in the project.

## Cleanup

`delete_project` is irreversible (its own description says so). Only
call it for genuinely throwaway/exploratory projects, and confirm with
the user first for anything real.

## Cost note

Stitch tool calls are token-heavy: `generate_screen_from_text`,
`edit_screens`, and `generate_variants` each return large payloads
(screenshots, full HTML, multi-turn tool exchanges). A single multi-step
workflow (e.g. two design systems + a screen) measured well over
1,000,000 tokens end-to-end in testing — size any token-budget grader
or context-window expectation accordingly, not against typical
lightweight-tool-call skills.
