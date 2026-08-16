<!--
Thanks for contributing. Nothing here is meant to be a hurdle — delete any
section that does not apply. A one-line typo fix needs a one-line description.
-->

## What this changes

<!-- What the change does, and why. If it fixes an issue, link it. -->

## How it was verified

<!--
Which of these you did. The suite passing is necessary but often not
sufficient: the failures a sidebar plugin produces are quiet ones — a tofu box,
a stale token, a fallback that never fires — and none of them raise anything.
-->

- [ ] `ruff check .` is clean
- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'` passes
- [ ] There is a test that fails without this change
- [ ] Ran against a live herdr session, with what I observed described below

<!-- If it changes what a user sees in the sidebar, paste the before and after. -->

## Contracts

<!-- Delete whichever section does not apply. -->

If you touched `agent_icons.py` or anything that talks to herdr:

- [ ] Everything reported still goes through `pane report-metadata` on the
      `harness_logo` token, and nothing calls `report-agent`, `--display-agent`,
      or `--state-label`
- [ ] `test_startup_reports_token_only_and_preserves_status_surface` still passes
- [ ] Nothing new is imported outside the standard library, and no executable is
      assumed to be on herdr's minimal `PATH`

If you touched `font/codepoints.toml`, `assets/`, or `tools/build_font.py`:

- [ ] No existing codepoint moved, and the glyph order is unchanged
- [ ] `dist/HerdrHarnessLogos-Regular.ttf` was rebuilt and committed, and
      `tests/test_font.py` passes against it
- [ ] Any new mark has its source path, pinned upstream commit, licence, and
      modification recorded in `assets/THIRD_PARTY_NOTICES.md`, with the full
      licence text present in `assets/licenses/`
- [ ] The README's codepoint table and the text fallbacks still agree with the
      code
