"""Non-destructive smoke test against the current icon-lab Herdr socket."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "test:herdr-agent-icons"
TOKEN = "harness_logo"


def herdr(*args: str) -> dict:
    result = subprocess.run(
        [os.environ.get("HERDR_BIN_PATH", "herdr"), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def main() -> int:
    socket = Path(os.environ.get("HERDR_SOCKET_PATH", ""))
    if (
        os.environ.get("HERDR_SESSION") != "icon-lab"
        or socket.name != "herdr.sock"
        or socket.parent.name != "icon-lab"
        or socket.parent.parent.name != "sessions"
    ):
        raise RuntimeError("live test is restricted to the current icon-lab Herdr socket")

    pane_id = os.environ["HERDR_PANE_ID"]
    before = herdr("pane", "get", pane_id)["result"]["pane"]
    agent = before.get("agent")
    if agent not in {"claude", "codex", "opencode", "omp"}:
        raise RuntimeError(f"current pane has unsupported agent {agent!r}")

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "agent_icons.py"),
                "--pane",
                pane_id,
                "--agent",
                agent,
                "--source",
                SOURCE,
                "--variant",
                "font",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        after = herdr("pane", "get", pane_id)["result"]["pane"]
        expected = {"claude": "\ue1a0", "codex": "\ue1a1", "opencode": "\ue1a2", "omp": "\ue1a3"}[agent]
        if after.get("tokens", {}).get(TOKEN) != expected:
            raise RuntimeError("Herdr did not expose the harness_logo token")
        if after.get("agent_status") != before.get("agent_status"):
            raise RuntimeError("display metadata changed Herdr semantic agent status")
        print(
            json.dumps(
                {
                    "socket": str(socket),
                    "pane_id": pane_id,
                    "agent": agent,
                    "harness_logo": after["tokens"][TOKEN],
                    "agent_status": after["agent_status"],
                },
                ensure_ascii=False,
            )
        )
    finally:
        herdr(
            "pane",
            "report-metadata",
            pane_id,
            "--source",
            SOURCE,
            "--clear-token",
            TOKEN,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
