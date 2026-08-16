# Herdr Harness Logos

A minimal Herdr v1 plugin that gives the sidebar recognizable monochrome harness marks for Claude, Codex, OpenCode, and OMP without taking over Herdr lifecycle state.

## Requirements

Herdr 0.8.0 or newer, and a `python3` of 3.11 or newer on the machine running
Herdr. The manifest invokes a bare `python3` with Herdr's minimal `PATH`, so the
runtime path imports nothing outside the standard library — 3.11 is the floor
only because `tomllib` arrived there. `fontTools` is needed to rebuild the font
and to run the font tests, never to run the plugin.

Linux, macOS, and Windows are declared. The `auto` variant uses Fontconfig
(`fc-match`) to decide whether the font is installed; where `fc-match` is
absent, `auto` stays on the text fallback and the font has to be selected
explicitly.

## How It Works

Herdr 0.8.0 metadata is plain text. `display_agent` does not accept ANSI, images, or styled spans. The plugin therefore reports one display-only pane token named `$harness_logo`:

| Harness | Font codepoint | Text fallback |
| --- | --- | --- |
| Claude | `U+E1A0` | `C` |
| Codex / OpenAI | `U+E1A1` | `AI` |
| OpenCode | `U+E1A2` | `OC` |
| OMP | `U+E1A3` | `OMP` |

The codepoints are stable BMP Private Use Area assignments. Every font glyph has a fixed 600-unit advance and is intended to occupy one terminal cell. The text fallback contains printable ASCII only.

The plugin never calls `report-agent`, changes `display_agent`, or reports state labels. Configure the sidebar with separate `state_icon`, `$harness_logo`, and `agent` tokens so Herdr retains its native colored lifecycle icon and semantic `idle`, `working`, `blocked`, `done`, or `unknown` state.

`variant = "auto"` is the default. On systems with Fontconfig, it uses the font only when the exact `Herdr Harness Logos` family is installed; otherwise it reports the text fallback. Set `variant = "font"` only after confirming the font preview. Set `variant = "text"` to force fallback or `variant = "none"` to clear the logo token.

## Preview First

Preview every font codepoint and fallback deterministically, without ANSI:

```sh
python3 preview.py
```

When the plugin is linked and enabled, open the same preview as a Herdr popup and pick a variant:

```sh
herdr plugin pane open --plugin moneycaringcoder.agent-icons --entrypoint preview
```

The popup writes only the plugin-owned `config.toml`. It does not edit Herdr or Ghostty configuration. To select explicitly outside the popup:

```sh
python3 preview.py --select font --config "$(herdr plugin config-dir moneycaringcoder.agent-icons)/config.toml"
```

Reapply the selection to panes that are already running:

```sh
herdr plugin action invoke refresh --plugin moneycaringcoder.agent-icons
```

## Ghostty Font Setup

Ghostty supports repeated `font-family` fallbacks and an explicit `font-codepoint-map`. Font changes affect new terminal surfaces. This repository does not install the font, edit Ghostty configuration, or restart Ghostty.

First preview `dist/HerdrHarnessLogos-Regular.ttf`, then install it manually.

Linux:

```sh
mkdir -p ~/.local/share/fonts
cp dist/HerdrHarnessLogos-Regular.ttf ~/.local/share/fonts/
fc-cache -f ~/.local/share/fonts
fc-match --format '%{family}\n' 'Herdr Harness Logos'
```

macOS:

```sh
mkdir -p ~/Library/Fonts
cp dist/HerdrHarnessLogos-Regular.ttf ~/Library/Fonts/
```

Add these lines to your Ghostty configuration manually. Keep your existing primary `font-family`; append the harness family as a fallback. If you currently rely on Ghostty's built-in default, make `JetBrains Mono` explicit first:

```ini
font-family = "JetBrains Mono"
font-family = "Herdr Harness Logos"
font-codepoint-map = U+E1A0-U+E1A3="Herdr Harness Logos"
```

Replace `JetBrains Mono` with your actual primary family when different. Do not reset the font list with `font-family = ""` unless you intentionally want to replace all existing fallbacks.

Open a new Ghostty window, tab, or split, then verify:

```sh
ghostty +list-fonts | grep -F 'Herdr Harness Logos'
ghostty +show-face --string=''
python3 preview.py
```

The literal characters in the `--string` argument are `U+E1A0` through `U+E1A3`. On macOS, where `fc-match` may be unavailable, select `font` explicitly after Ghostty confirms the face; `auto` deliberately remains on the safe text fallback when it cannot verify the family.

To uninstall manually, remove the copied TTF, refresh Fontconfig on Linux, remove the two Ghostty lines, and open a new terminal surface.

## Herdr Sidebar

Herdr can style an entire sidebar token, not spans inside `display_agent`. Keeping the logo in `$harness_logo` allows independent color while preserving the native agent label.

The most theme-safe configuration inherits the current theme foreground:

```toml
[ui.sidebar.agents]
rows = [
  ["state_icon", { token = "$harness_logo", bold = true }, "agent"],
  ["workspace", "tab"],
]
```

Restrained per-harness color is supported through `rows_by_agent`. Colors are fixed hex values, so choose values with sufficient contrast for your active light or dark theme.

Dark-theme example:

```toml
[ui.sidebar.agents.rows_by_agent]
claude = [["state_icon", { token = "$harness_logo", fg = "#d97757" }, "agent"], ["workspace", "tab"]]
codex = [["state_icon", { token = "$harness_logo", fg = "#74aa9c" }, "agent"], ["workspace", "tab"]]
opencode = [["state_icon", { token = "$harness_logo", fg = "#a8a29e" }, "agent"], ["workspace", "tab"]]
omp = [["state_icon", { token = "$harness_logo", fg = "#f97316" }, "agent"], ["workspace", "tab"]]
```

Light-theme alternatives are `#a3412c`, `#2f6f62`, `#57534e`, and `#c2410c` in the same order. Herdr 0.8.0 has no semantic color reference inside an inline sidebar token and cannot automatically switch these per-agent hex colors with the theme. Omit `fg` for fully theme-safe styling.

After manually changing Herdr's sidebar rows, `herdr server reload-config` applies that reloadable configuration without restarting Herdr or its panes.

## Font Sources And Licensing

The font is generated from exact repository-owned marks:

- Claude: Anthropic `cwc-workshops`, Apache-2.0.
- Codex: OpenAI `codex`, Apache-2.0.
- OpenCode: anomalyco `opencode`, MIT.
- OMP: can1357 `oh-my-pi`, MIT.

Exact source paths, pinned commits where available, modifications, copyright notices, trademark caveats, and complete license texts are in `assets/THIRD_PARTY_NOTICES.md` and `assets/licenses/`. The marks identify third-party products and do not imply affiliation or endorsement.

Rebuild the deterministic font in an isolated environment:

```sh
python3 -m venv .venv-font
.venv-font/bin/pip install -r requirements-font.txt
.venv-font/bin/python tools/build_font.py
```

## Test

Runtime tests have no third-party dependencies:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

Run font structure and reproducibility tests in the font build environment:

```sh
.venv-font/bin/python -m unittest tests.test_font
```

`tests/live_icon_lab.py` is not part of the discovered suite. It talks to a real Herdr and refuses to run unless both `HERDR_SESSION=icon-lab` and `HERDR_SOCKET_PATH` is under `/sessions/icon-lab/`:

```sh
python3 tests/live_icon_lab.py
```

It reports a test-owned `$harness_logo`, confirms that `agent_status` is unchanged, and clears the token in a `finally` block.

Lint with the pinned ruff:

```sh
python3 -m pip install -r requirements-lint.txt
ruff check .
```

CI runs the lint, the runtime suite on Linux and macOS against Python 3.11 and 3.13, and the font job, which rebuilds the TTF and fails if it differs from the committed one.

## Installation Scope

After reviewing the manifest and scripts, use Herdr's normal local-plugin workflow if desired. This repository does not install, link, enable, configure, reload, restart, or stop Herdr automatically.

## Project

Changes are recorded in [CHANGELOG.md](CHANGELOG.md). [CONTRIBUTING.md](CONTRIBUTING.md) covers the two contracts that matter — the plugin owns one token and nothing else, and a codepoint assignment is permanent — and [SECURITY.md](SECURITY.md) covers what to report privately.

This project's own code and documentation are under the [MIT licence](LICENSE). The harness marks, and the font built from them, carry their upstream Apache-2.0 and MIT terms; see `assets/THIRD_PARTY_NOTICES.md` and `assets/licenses/`.
