#!/usr/bin/env python3
"""Verify that a release tag matches every version surface, and collect the notes.

Run with no arguments in a checkout of a tag and it reads `GITHUB_REF_NAME`;
run it with `--tag vX.Y.Z` anywhere to rehearse a release that does not exist
yet.

This plugin has no `Cargo.toml`. Its version lives in `herdr-plugin.toml`,
which is what the marketplace displays, and in `CHANGELOG.md`. Both have to
agree with the tag before anything is published.

Deliberately *not* checked: `font/codepoints.toml`. The bundled typeface
carries its own version, which tracks the marks it contains rather than the
plugin around them, and tying the two together would force a pointless font
rebuild on every plugin release — and a font rebuild changes a binary artifact
users install. `tests/test_font.py` already asserts that the committed
`dist/` file equals a fresh build, which is the property that actually matters.

The changelog section for the released version has to exist, be dated, and
actually say something. `--notes-out` writes it to a file, so the published
release notes are the changelog rather than a second description of the same
change that can disagree with it.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - guarded for old interpreters
    print("release identity error: this script requires Python 3.11+", file=sys.stderr)
    raise SystemExit(1) from None

ROOT = Path(__file__).resolve().parents[1]

VERSION = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
TAG = re.compile(rf"v{VERSION}")


class ReleaseError(ValueError):
    pass


def load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except OSError as error:
        raise ReleaseError(f"{path.name} cannot be read") from error
    except tomllib.TOMLDecodeError as error:
        raise ReleaseError(f"{path.name} is not valid TOML: {error}") from error


def resolve_tag(explicit: str | None, environment: str | None) -> str:
    tag = explicit if explicit is not None else environment
    if not tag:
        raise ReleaseError("provide --tag v<version>, or run with GITHUB_REF_NAME set")
    if not TAG.fullmatch(tag):
        raise ReleaseError(f"tag {tag!r} is not v<major>.<minor>.<patch>")
    return tag


def check_release_context(
    tag: str,
    *,
    github_actions: bool,
    ref_type: str | None,
    ref_name: str | None,
) -> None:
    """In CI, refuse to publish from anything but the exact tag being validated."""
    if not github_actions:
        return
    if ref_type != "tag" or ref_name != tag:
        raise ReleaseError(f"a release run must be triggered by the {tag} tag itself")


def plugin_version(root: Path) -> str:
    version = load_toml(root / "herdr-plugin.toml").get("version")
    if not isinstance(version, str):
        raise ReleaseError("herdr-plugin.toml has no version string")
    return version


def changelog_notes(text: str, version: str) -> str:
    """The body of one dated changelog section, or a refusal to publish."""
    heading = re.compile(rf"^## \[{re.escape(version)}\] - (\d{{4}}-\d{{2}}-\d{{2}})\s*$", re.MULTILINE)
    match = heading.search(text)
    if match is None:
        if re.search(rf"^## \[{re.escape(version)}\]", text, re.MULTILINE):
            raise ReleaseError(f"CHANGELOG.md has a [{version}] heading but no ISO-8601 date on it")
        raise ReleaseError(f"CHANGELOG.md has no dated [{version}] section")
    rest = text[match.end() :]
    next_section = re.search(r"^## ", rest, re.MULTILINE)
    body = rest[: next_section.start()] if next_section else rest
    # A section carrying only sub-headings is empty for a reader's purposes, and
    # publishing it produces a release page that says "### Added" and nothing
    # else. Require at least one line that is not blank and not a heading.
    if not any(line.strip() and not line.lstrip().startswith("#") for line in body.splitlines()):
        raise ReleaseError(f"CHANGELOG.md section for [{version}] is empty")
    return body.strip("\n") + "\n"


def check(root: Path, tag: str) -> str:
    version = tag[1:]
    manifest_version = plugin_version(root)
    if manifest_version != version:
        raise ReleaseError(
            f"herdr-plugin.toml version {manifest_version!r} does not match tag {tag!r}. "
            "This is the version the marketplace displays."
        )
    try:
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError as error:
        raise ReleaseError("CHANGELOG.md cannot be read") from error
    return changelog_notes(changelog, version)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a release tag against every version surface")
    parser.add_argument("--tag", help="release tag to verify; defaults to GITHUB_REF_NAME")
    parser.add_argument("--notes-out", type=Path, help="write the changelog section for this version here")
    args = parser.parse_args()
    try:
        tag = resolve_tag(args.tag, os.environ.get("GITHUB_REF_NAME"))
        check_release_context(
            tag,
            github_actions=os.environ.get("GITHUB_ACTIONS") == "true",
            ref_type=os.environ.get("GITHUB_REF_TYPE"),
            ref_name=os.environ.get("GITHUB_REF_NAME"),
        )
        notes = check(ROOT, tag)
        if args.notes_out is not None:
            args.notes_out.write_text(notes, encoding="utf-8")
    except ReleaseError as error:
        print(f"release identity error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except OSError as error:
        print(f"release identity error: notes could not be written: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(f"release identity verified: {tag}")


if __name__ == "__main__":
    main()
