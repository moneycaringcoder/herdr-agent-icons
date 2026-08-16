from __future__ import annotations

import ast
import json
import os
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent_icons
import preview


class AgentIconsTests(unittest.TestCase):
    def test_stable_font_mapping(self) -> None:
        self.assertEqual(
            {agent: f"U+{ord(glyph):04X}" for agent, glyph in agent_icons.PUA_LOGOS.items()},
            {
                "claude": "U+E1A0",
                "codex": "U+E1A1",
                "opencode": "U+E1A2",
                "omp": "U+E1A3",
            },
        )

    def test_auto_falls_back_to_text_when_font_is_missing(self) -> None:
        with mock.patch.object(agent_icons, "font_available", return_value=False):
            self.assertEqual(agent_icons.logo_for("claude", "auto"), "C")
            self.assertEqual(agent_icons.logo_for("codex", "auto"), "AI")
            self.assertEqual(agent_icons.logo_for("opencode", "auto"), "OC")
            self.assertEqual(agent_icons.logo_for("omp", "auto"), "OMP")

    def test_all_variants_are_narrow_printable_text(self) -> None:
        for logo in (*agent_icons.PUA_LOGOS.values(), *agent_icons.TEXT_LOGOS.values()):
            self.assertGreaterEqual(agent_icons.cell_width(logo), 1)
            self.assertLessEqual(agent_icons.cell_width(logo), 3)
            self.assertNotIn("\ufe0f", logo)
        for logo in agent_icons.PUA_LOGOS.values():
            self.assertEqual(agent_icons.cell_width(logo), 1)

    def test_unsupported_agent_clears_owned_token(self) -> None:
        with mock.patch.object(agent_icons, "run_herdr", return_value={}) as run:
            self.assertFalse(agent_icons.report_logo("herdr", "test:icons", "w1:p1", "gemini", "font"))
        self.assertEqual(
            run.call_args.args,
            (
                "herdr",
                "pane",
                "report-metadata",
                "w1:p1",
                "--source",
                "test:icons",
                "--clear-token",
                "harness_logo",
            ),
        )

    def test_event_pane_accepts_event_envelope(self) -> None:
        raw = json.dumps({"event": {"type": "pane_agent_detected", "pane_id": "w1:p4", "agent": "omp"}})
        self.assertEqual(agent_icons.event_pane(raw), "w1:p4")

    def test_startup_reports_token_only_and_preserves_status_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            calls_path = directory_path / "calls.jsonl"
            fake_herdr = directory_path / "herdr"
            fake_herdr.write_text(
                """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["CALLS_PATH"], "a", encoding="utf-8") as calls:
    calls.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:] == ["pane", "list"]:
    print(json.dumps({"result": {"panes": [
        {"pane_id": "w1:p1", "agent": "claude"},
        {"pane_id": "w1:p2", "agent": "codex"},
        {"pane_id": "w1:p3", "agent": "opencode"},
        {"pane_id": "w1:p4", "agent": "omp"},
        {"pane_id": "w1:p5", "agent": "gemini"}
    ]}}))
""",
                encoding="utf-8",
            )
            fake_herdr.chmod(fake_herdr.stat().st_mode | stat.S_IXUSR)
            env = os.environ.copy()
            env.update(
                HERDR_BIN_PATH=str(fake_herdr),
                HERDR_PLUGIN_ID="moneycaringcoder.agent-icons",
                CALLS_PATH=str(calls_path),
            )
            env.pop("HERDR_PLUGIN_EVENT_JSON", None)

            result = subprocess.run(
                [sys.executable, str(ROOT / "agent_icons.py"), "--variant", "font"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in calls_path.read_text().splitlines()]
            self.assertEqual(len(calls), 6)
            reports = calls[1:]
            self.assertEqual(
                [report[-1] for report in reports[:4]],
                [
                    "harness_logo=\ue1a0",
                    "harness_logo=\ue1a1",
                    "harness_logo=\ue1a2",
                    "harness_logo=\ue1a3",
                ],
            )
            self.assertEqual(reports[4][-2:], ["--clear-token", "harness_logo"])
            for report in reports:
                self.assertEqual(report[:2], ["pane", "report-metadata"])
                self.assertNotIn("report-agent", report)
                self.assertNotIn("--display-agent", report)
                self.assertNotIn("--state-label", report)

    def test_unresolvable_herdr_binary_is_reported_not_raised(self) -> None:
        # Herdr runs plugin commands with a minimal PATH. If HERDR_BIN_PATH is
        # missing and `herdr` is not on that PATH, the plugin must fail with a
        # message rather than a traceback.
        env = os.environ.copy()
        env.update(HERDR_BIN_PATH="herdr-does-not-exist", PATH="")
        env.pop("HERDR_PLUGIN_EVENT_JSON", None)

        result = subprocess.run(
            [sys.executable, str(ROOT / "agent_icons.py"), "--variant", "font"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("herdr-does-not-exist", result.stderr)

    def test_runtime_imports_are_standard_library_only(self) -> None:
        # The manifest invokes a bare `python3` with a minimal PATH, so nothing
        # on the runtime path may import out of the font build virtual
        # environment. fontTools belongs to tools/ and tests/test_font.py only.
        local = {"agent_icons", "preview"}
        for module in ("agent_icons.py", "preview.py"):
            tree = ast.parse((ROOT / module).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    root = name.split(".", 1)[0]
                    with self.subTest(module=module, imported=name):
                        self.assertIn(root, sys.stdlib_module_names | local)

    def test_preview_is_deterministic_and_contains_all_variants(self) -> None:
        with mock.patch.object(preview, "font_available", return_value=False):
            first = preview.preview()
            second = preview.preview()
        self.assertEqual(first, second)
        for value in ("Claude", "Codex", "OpenCode", "OMP", "U+E1A0", "U+E1A3"):
            self.assertIn(value, first)
        self.assertNotIn("\x1b", first)

    def test_manifest_declares_one_shot_hooks_and_preview(self) -> None:
        manifest = tomllib.loads((ROOT / "herdr-plugin.toml").read_text())
        self.assertEqual(manifest["id"], "moneycaringcoder.agent-icons")
        self.assertEqual(manifest["min_herdr_version"], "0.8.0")
        self.assertEqual(manifest["startup"], [{"command": ["python3", "agent_icons.py"]}])
        self.assertEqual(manifest["events"][0]["on"], "pane.agent_detected")
        self.assertEqual(manifest["actions"][0]["id"], "refresh")
        self.assertEqual(manifest["panes"][0]["id"], "preview")


if __name__ == "__main__":
    unittest.main()
