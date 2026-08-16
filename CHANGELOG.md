# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-08-16

First public release. Earlier versions existed only locally and were never
published, so this section describes the plugin as it now behaves rather than
the path it took to get here.

### Added

- A display-only `$harness_logo` pane token carrying a recognisable monochrome
  mark for Claude, Codex, OpenCode, and OMP. The plugin never calls
  `report-agent`, never touches `display_agent`, and never reports a state
  label, so Herdr keeps its native coloured lifecycle icon and its semantic
  `idle`, `working`, `blocked`, `done`, and `unknown` states.
- Four variants, selected through the plugin's own `config.toml`. `auto` is the
  default and uses the font only where Fontconfig finds the exact `Herdr Harness
  Logos` family installed, falling back to printable ASCII otherwise. `font`
  forces the marks, `text` forces the fallback, and `none` clears the token.
- Stable Private Use Area assignments — `U+E1A0` Claude, `U+E1A1` Codex,
  `U+E1A2` OpenCode, `U+E1A3` OMP — with `C`, `AI`, `OC`, and `OMP` as the text
  fallbacks. Every font glyph has a fixed 600-unit advance and occupies exactly
  one terminal cell.
- `dist/HerdrHarnessLogos-Regular.ttf`, a deterministic font built by
  `tools/build_font.py` from the four SVG marks in `assets/svg/`. The build is
  reproducible byte for byte, and a test asserts that the committed file matches
  a fresh build.
- A startup hook that applies the token to every pane Herdr already knows about,
  and a `pane.agent_detected` event hook that applies it to panes as they are
  recognised. Both are one-shot commands rather than daemons.
- A `refresh` action that reapplies the selected variant to running panes, and a
  `preview` popup pane that renders every codepoint and fallback without ANSI
  and writes the chosen variant to the plugin's own configuration.
- `assets/THIRD_PARTY_NOTICES.md` and `assets/licenses/`, recording the source,
  pinned commit, licence, and modification for each mark, along with the
  complete Apache-2.0 and MIT texts.
- A live smoke test, `tests/live_icon_lab.py`, that refuses to run outside a
  session named `icon-lab`, confirms Herdr exposes the token, confirms
  `agent_status` is unchanged, and clears the token in a `finally` block.

### Notes

- The plugin id is `moneycaringcoder.agent-icons`. The runtime path imports only
  the standard library, so the manifest's bare `python3` works under Herdr's
  minimal `PATH` without a virtual environment; `fontTools` is needed to rebuild
  the font, never to run the plugin.
- The font is not installed for you. This repository does not write to
  Fontconfig, edit Ghostty's configuration, or restart a terminal.
