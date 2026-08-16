#!/usr/bin/env python3
"""Verify Herdr's CLI reference still documents the commands this plugin runs.

This is the weaker half of the upstream canary, and it is worth saying why it
exists at all and why it is separate.

`herdr_api_contract.py` checks the data contract against a schema Herdr
generates from its own types and enforces with a test, so it cannot drift.
This plugin, though, does not open the socket: it shells out to the binary at
`HERDR_BIN_PATH` and runs three commands. The subcommand and flag *spellings*
are not in that schema, and a rename of `pane report-metadata` or `--clear-token`
would break every code path here while the schema stayed identical.

The only machine-readable statement of that surface outside a built binary is
Herdr's published CLI reference. It is prose, and nothing upstream asserts it
against the real parser, so this check is documentation-derived rather than
type-derived. To keep that from producing noise, it looks only for exact
invocation fragments that a rewording would not disturb and a rename would.
A failure here means "read the CLI reference", not "Herdr is broken".
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

MAX_REFERENCE_BYTES = 1024 * 1024

# Exact fragments, each one a thing this plugin types at the binary.
#
# `agent_icons.py` runs:
#   herdr pane get <pane_id>
#   herdr pane list
#   herdr pane report-metadata <pane_id> --source ID --token NAME=VALUE
#   herdr pane report-metadata <pane_id> --source ID --clear-token NAME
REQUIRED_FRAGMENTS: tuple[tuple[str, str], ...] = (
    ("herdr pane get", "reading one pane's current agent"),
    ("herdr pane list", "enumerating panes at startup"),
    ("herdr pane report-metadata", "setting and clearing the logo token"),
    ("--source", "identifying this plugin as the metadata source"),
    ("--token", "setting the logo token"),
    ("--clear-token", "removing the logo token when a pane has no agent"),
)


class CliContractError(ValueError):
    pass


def read_reference(path: Path) -> str:
    """Read one regular file as bounded, strict UTF-8 text."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise CliContractError("CLI reference input must be a regular file")
        if metadata.st_size > MAX_REFERENCE_BYTES:
            raise CliContractError(f"CLI reference exceeds {MAX_REFERENCE_BYTES}-byte limit")
        handle = os.fdopen(descriptor, "rb")
        descriptor = None
        with handle:
            content = handle.read(MAX_REFERENCE_BYTES + 1)
    except CliContractError:
        raise
    except OSError as error:
        raise CliContractError("CLI reference cannot be read") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(content) > MAX_REFERENCE_BYTES:
        raise CliContractError(f"CLI reference exceeds {MAX_REFERENCE_BYTES}-byte limit")
    try:
        return content.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise CliContractError("CLI reference is not valid UTF-8") from error


def validate(reference: str) -> int:
    # A document that no longer mentions the binary at all is far more likely to
    # be a 404 page or a moved file than a real CLI change, and treating it as a
    # long list of renames would bury the actual cause.
    if "herdr pane" not in reference:
        raise CliContractError("input does not look like Herdr's CLI reference")
    missing = [f"`{fragment}` ({why})" for fragment, why in REQUIRED_FRAGMENTS if fragment not in reference]
    if missing:
        raise CliContractError("CLI reference no longer documents: " + "; ".join(missing))
    return len(REQUIRED_FRAGMENTS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Herdr's CLI against agent-icons' needs")
    parser.add_argument("reference", type=Path, help="path to cli-reference.mdx")
    args = parser.parse_args()
    try:
        count = validate(read_reference(args.reference))
    except CliContractError as error:
        print(f"Herdr CLI contract error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(f"Herdr CLI contract verified: {count} documented fragments")


if __name__ == "__main__":
    main()
