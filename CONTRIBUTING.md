# Contributing to agent-icons

Contributions are genuinely welcome — bug reports, questions, documentation
fixes, and code. This document exists so you know what to expect before you
spend time on something, not to put obstacles in front of you.

The project is maintained by one person. Review is attentive but not instant,
and every change is read carefully before it lands. Please don't take questions
on a pull request as resistance; they are how the maintainer stays confident in
a plugin that writes into other people's terminal sidebars.

## The two rules that matter

**1. The plugin owns one token and nothing else.** Everything it reports goes
through `pane report-metadata --token harness_logo=…` or
`--clear-token harness_logo`. It must never call `report-agent`, never set
`--display-agent`, and never set `--state-label`. Herdr's coloured lifecycle
icon and its semantic `idle`, `working`, `blocked`, `done`, and `unknown` states
are Herdr's, and a decorative plugin that overwrites them takes away information
the user actually needs.

`tests/test_agent_icons.py::test_startup_reports_token_only_and_preserves_status_surface`
enforces this by running the real script against a fake `herdr` and asserting on
every argument vector it produced. If your change makes that test fail, the test
is right and the change is wrong.

**2. A codepoint assignment is permanent.** `U+E1A0` through `U+E1A3` are a
published contract. Users have put `font-codepoint-map = U+E1A0-U+E1A3=…` into
their Ghostty configuration and installed a font built against that order. New
harnesses get new codepoints appended; existing ones do not move, and the glyph
order in `font/codepoints.toml` does not change. `tools/build_font.py` refuses
to build if the order changes, deliberately.

## Getting set up

```sh
git clone https://github.com/moneycaringcoder/herdr-agent-icons
cd herdr-agent-icons
python3 -m unittest discover -s tests -p 'test_*.py'
herdr plugin link .
```

The runtime needs nothing but a `python3` of 3.11 or newer. Herdr invokes plugin
commands with a minimal `PATH` and a bare `python3`, so **nothing on the runtime
path may import a third-party module.** `agent_icons.py` and `preview.py` are
standard library only, and a test parses their imports to keep them that way.
`fontTools` belongs to `tools/` and `tests/test_font.py`.

To work on the font:

```sh
python3 -m venv .venv-font
.venv-font/bin/pip install -r requirements-font.txt
.venv-font/bin/python tools/build_font.py
.venv-font/bin/python -m unittest tests.test_font
```

Before opening a pull request:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
.venv-font/bin/python -m unittest tests.test_font   # if you touched the font
```

CI runs exactly these on Linux and macOS, and also rebuilds the font and
compares it byte for byte against the committed `dist/` file. A font change that
does not include the rebuilt TTF will fail there.

No test requires a running Herdr. `tests/test_agent_icons.py` stands up a fake
`herdr` executable in a temporary directory and records what the plugin asked it
to do.

`tests/live_icon_lab.py` is the exception and is not part of the suite. It talks
to a real Herdr, and it refuses to run unless `HERDR_SESSION` is `icon-lab` and
`HERDR_SOCKET_PATH` sits under `/sessions/icon-lab/`, so it cannot touch a
session you were working in. It clears its token in a `finally` block.

Run it before a release. CI cannot: it needs a live Herdr with a recognised
agent in a pane, which no runner has. That makes it the only check that the
whole path actually works — the fake `herdr` in the suite proves the plugin
asks for the right thing, not that Herdr answers.

Start the session from a terminal that is **not** already inside Herdr, because
Herdr refuses to nest unless `[experimental] allow_nested` is set:

```sh
herdr --session icon-lab
```

Then, from anywhere, put a supported agent in a pane of that session and point
the test at it:

```sh
HERDR_SOCKET_PATH=~/.config/herdr/sessions/icon-lab/herdr.sock \
  herdr agent start iconlab --kind claude --pane <pane-id>

HERDR_SESSION=icon-lab \
HERDR_SOCKET_PATH=~/.config/herdr/sessions/icon-lab/herdr.sock \
HERDR_PANE_ID=<pane-id> \
  python3 tests/live_icon_lab.py
```

It prints one JSON line and exits `0`. The `harness_logo` value in that line
looks blank in most terminals — it is a private-use codepoint, and a font that
has no glyph for it renders nothing. Blank output there is expected and is not
the test passing vacuously: the assertion compares against the exact expected
codepoint, so a missing or wrong token fails. To see the value itself, read the
token back with `herdr pane get <pane-id>` while it is set.

Last run: 2026-08-16, against Herdr 0.8.0, with a `claude` agent. Update this
line when you run it, so a stale pass is visible as stale.

## What makes a change easy to merge

**A test that fails before your fix and passes after it.** This matters here
because the failures a sidebar plugin produces are quiet ones: a tofu box where a
glyph should be, a stale token on a pane that changed harness, a fallback that
silently never fires. None of those raise anything.

**Fallbacks that stay conservative.** `auto` reports text unless it can *verify*
that the exact `Herdr Harness Logos` family is installed. Guessing wrong there
puts an unreadable box in the sidebar of someone who never asked for a font, so
a change that makes `auto` more optimistic needs a strong argument.

**No assumptions about the environment.** Herdr runs plugin commands with a
minimal `PATH`. `fc-match` may be missing, `herdr` may not be resolvable without
`HERDR_BIN_PATH`, and neither may produce a traceback. Absence is a normal
outcome to be handled, not an error to be raised.

**Marks with their paperwork.** A new harness mark needs its source path, its
pinned upstream commit, its licence, and the modification you made recorded in
`assets/THIRD_PARTY_NOTICES.md`, with the full licence text in
`assets/licenses/` if it is not already there. A mark whose provenance cannot be
established will not be merged, however good it looks.

**Small, focused pull requests.** One behaviour change per pull request, with
the reasoning in the commit message rather than in a comment on the diff.

## What the project will probably say no to

- **Taking over `display_agent` or the state icon.** That is the whole point of
  the design. A plugin that replaces Herdr's lifecycle state is a different,
  worse plugin.
- **Colour or ANSI inside the token.** Herdr 0.8.0 metadata is plain text.
  Styling belongs in the user's sidebar row configuration, where it can be a
  theme-safe choice rather than a hardcoded hex value the plugin imposed.
- **Installing the font for the user.** Writing into a font directory, running
  `fc-cache`, editing a Ghostty configuration, or restarting a terminal are all
  things this repository deliberately does not do.
- **Third-party dependencies on the runtime path.** There are none, and Herdr's
  minimal `PATH` is why.
- **Moving an existing codepoint.** See rule two.

## Style

Match the code around you. Comments explain *why*, especially where the code
looks odd because of something Herdr, Fontconfig, or OpenType actually does.

Commit messages are plain prose in the imperative, wrapped at 72 columns, and
say what changed and why.

## Code of conduct

By participating you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).
