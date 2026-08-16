# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Licensed terminal marks for Cline, MastraCode, Kimi Code CLI, Kilo Code, and
  Maki, appended at `U+E1A4` through `U+E1A8` without moving the four published
  assignments. Herdr-recognized harnesses without a safely reusable mark remain
  deliberately unmarked.
- Tag-triggered release automation. Pushing `vX.Y.Z` runs the lint, test and
  font jobs and publishes the GitHub release with notes taken from that
  version's changelog section — but only after an identity gate has confirmed
  that the tag and `herdr-plugin.toml` name the same version and that the
  changelog section for it exists and is not empty. The manifest version is the
  one the marketplace displays. The bundled typeface keeps its own independent
  version, which tracks the marks it contains rather than the plugin around
  them.
- An advisory upstream canary. Once a day it resolves one exact herdr `master`
  commit and checks two things against it: the API schema herdr generates from
  its own types, for the three methods behind the CLI commands this plugin runs
  and the pane fields it reads, and herdr's CLI reference, for the subcommand
  and flag spellings — which are not in the schema and would break every code
  path here if they were renamed. It is scheduled and manual only, it is not a
  required check, and a red canary is a signal to read herdr's recent changes
  rather than a reason to hold a pull request.

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
