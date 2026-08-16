#!/usr/bin/env python3
"""Offline tests for the CLI half of agent-icons' upstream canary.

Same purpose as the API-contract tests: prove the check can fail. Each declared
fragment is removed in turn and asserted to produce a non-zero exit, so a
fragment the checker does not enforce breaks a test.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from herdr_cli_contract import (  # noqa: E402
    MAX_REFERENCE_BYTES,
    REQUIRED_FRAGMENTS,
    CliContractError,
    read_reference,
    validate,
)

CHECKER = Path(__file__).with_name("herdr_cli_contract.py")

# A stand-in for the published reference, carrying every fragment the plugin
# needs and some surrounding prose, so that "removing a fragment" is a real
# edit rather than emptying the document.
REFERENCE = """
## Panes

herdr pane list [--workspace <workspace_id>]
herdr pane get <pane_id>

## Metadata

herdr pane report-metadata <pane_id> \\
  --source ID \\
  [--token NAME=VALUE] \\
  [--clear-token NAME] \\
  [--ttl-ms N]

`--token` patches one named display value; `--clear-token` removes one.
"""


class ReferenceTests(unittest.TestCase):
    def test_a_reference_carrying_every_fragment_passes(self) -> None:
        self.assertEqual(validate(REFERENCE), len(REQUIRED_FRAGMENTS))

    def test_unrelated_documentation_changes_are_tolerated(self) -> None:
        rewritten = REFERENCE.replace("## Metadata", "## Reporting pane metadata")
        rewritten += "\nherdr pane split <pane_id> --direction right\n"
        self.assertEqual(validate(rewritten), len(REQUIRED_FRAGMENTS))

    def test_each_missing_fragment_is_caught(self) -> None:
        for fragment, _ in REQUIRED_FRAGMENTS:
            with self.subTest(fragment=fragment):
                damaged = REFERENCE.replace(fragment, "herdr pane REDACTED")
                with self.assertRaisesRegex(CliContractError, "no longer documents"):
                    validate(damaged)

    def test_a_renamed_subcommand_is_caught(self) -> None:
        renamed = REFERENCE.replace("report-metadata", "set-metadata")
        with self.assertRaisesRegex(CliContractError, "report-metadata"):
            validate(renamed)

    def test_something_that_is_not_the_reference_fails_with_one_clear_reason(self) -> None:
        for content in ("", "<!DOCTYPE html><title>404: Not Found</title>", "# Configuration"):
            with self.subTest(content=content):
                with self.assertRaisesRegex(CliContractError, "does not look like Herdr's CLI reference"):
                    validate(content)


class InputTests(unittest.TestCase):
    def run_checker(self, content: bytes) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "cli-reference.mdx"
            reference.write_bytes(content)
            return subprocess.run(
                [sys.executable, str(CHECKER), str(reference)],
                capture_output=True,
                check=False,
                text=True,
            )

    def test_a_good_reference_exits_zero(self) -> None:
        result = self.run_checker(REFERENCE.encode())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            f"Herdr CLI contract verified: {len(REQUIRED_FRAGMENTS)} documented fragments\n",
        )

    def test_a_damaged_reference_exits_one(self) -> None:
        result = self.run_checker(REFERENCE.replace("--clear-token", "--unset").encode())
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("--clear-token", result.stderr)

    def test_non_utf8_input_is_rejected(self) -> None:
        result = self.run_checker(b"herdr pane get \xff")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not valid UTF-8", result.stderr)

    def test_an_oversized_file_is_rejected_before_scanning(self) -> None:
        result = self.run_checker(b"x" * (MAX_REFERENCE_BYTES + 1))
        self.assertEqual(result.returncode, 1)
        self.assertIn("byte limit", result.stderr)

    def test_a_directory_is_rejected_without_disclosing_its_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(CliContractError, "regular file") as raised:
                read_reference(Path(directory))
            self.assertNotIn(directory, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
