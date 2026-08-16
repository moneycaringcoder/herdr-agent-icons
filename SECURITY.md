# Security policy

## Reporting a vulnerability

Please report security issues privately, through GitHub's
[private vulnerability reporting](https://github.com/moneycaringcoder/herdr-agent-icons/security/advisories/new)
rather than as a public issue.

You can expect an acknowledgement within a few days. Since this is a
single-maintainer project, please don't read silence as dismissal — follow up if
you have heard nothing after a week.

If you would rather not use GitHub's reporting flow, open a public issue saying
only that you have found a security problem and would like a private channel,
with no details, and one will be arranged.

## What counts as a security issue here

agent-icons is a decorative plugin, but it runs on every pane Herdr starts and
it ships a font binary that users install into their systems. That is where the
sharp edges are.

- **Anything the plugin writes outside its own token or its own configuration
  file.** It reports `harness_logo` through `pane report-metadata` and writes one
  `variant = …` line to the config directory Herdr gives it. A path that writes
  anywhere else — a font directory, a Ghostty configuration, Herdr's own
  configuration, any file outside `HERDR_PLUGIN_CONFIG_DIR` — is a bug.
- **Anything that executes a binary the user did not intend.** The plugin runs
  `herdr` from `HERDR_BIN_PATH` and `fc-match` resolved through `shutil.which`.
  Both are invoked as argv arrays, never through a shell. A way to get a
  different executable run — through a config value, an event payload, an agent
  name, or a relative path resolved against an attacker-controlled directory —
  is in scope.
- **Anything that turns event or pane data into a command.** Pane ids and agent
  names arrive from Herdr as JSON and are passed straight into an argv array. A
  value that escapes that and becomes an option, an argument to a different
  subcommand, or a shell fragment is a serious bug.
- **A font that does anything a font should not.** `dist/HerdrHarnessLogos-Regular.ttf`
  is built from four SVG paths in this repository and contains only outline
  tables. If a build produces a font carrying anything else — hinting bytecode
  that is not ours, an embedded colour or bitmap table, or a table the contract
  test does not expect — say so.
- **A mark with unestablished provenance.** Every mark in `assets/svg/` traces to
  a pinned upstream commit under a recorded licence in
  `assets/THIRD_PARTY_NOTICES.md`. A mark that does not, or a notice that
  misstates a licence, is a legal defect and is treated with the same urgency.
- **Leaking terminal contents.** The plugin makes no network calls at all, and
  it reads only what `herdr pane list` and `herdr pane get` return. Any outbound
  traffic is a bug by definition.

## What is out of scope

- A tofu box in the sidebar because the font is not installed or Ghostty is not
  configured for the codepoint range. That is what `auto` and the text fallback
  exist for; a report is welcome as an ordinary issue.
- Disagreement about which glyph a harness should have, or how a mark was
  simplified for one terminal cell.
- A hex colour in the README's sidebar examples that reads poorly against your
  theme. Omit `fg` for theme-safe styling.
- The plugin reading a `config.toml` you wrote yourself.
- Issues in Herdr, Fontconfig, or Ghostty. Those belong upstream, though a
  report here is welcome if this plugin could work around one.

## Supported versions

The most recent release is supported. Given the size of the project, fixes are
made on `main` and released rather than backported.
