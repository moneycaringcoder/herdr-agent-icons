#!/usr/bin/env python3
"""Apply display-only icons to Herdr agent names."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
import unicodedata
from pathlib import Path
from typing import Any

FONT_FAMILY = "Herdr Harness Logos"
TOKEN_NAME = "harness_logo"
PUA_LOGOS = {
    "claude": "\ue1a0",
    "codex": "\ue1a1",
    "opencode": "\ue1a2",
    "omp": "\ue1a3",
}
TEXT_LOGOS = {
    "claude": "C",
    "codex": "AI",
    "opencode": "OC",
    "omp": "OMP",
}
VARIANTS = ("auto", "font", "text", "none")


def run_herdr(herdr: str, *args: str) -> dict[str, Any]:
    # Herdr runs plugin commands with a minimal PATH, so `herdr` is not
    # necessarily resolvable from it. HERDR_BIN_PATH is the supported way in,
    # and its absence has to read as a plain message rather than a traceback.
    try:
        result = subprocess.run(
            [herdr, *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise RuntimeError(f"could not run {herdr!r}: {error}") from error
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or f"Herdr exited with status {result.returncode}")
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def cell_width(text: str) -> int:
    width = 0
    for character in text:
        if unicodedata.category(character).startswith("C") and not (0xE000 <= ord(character) <= 0xF8FF):
            raise ValueError(f"non-printing character U+{ord(character):04X}")
        if unicodedata.combining(character):
            continue
        width += 2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1
    return width


def font_available() -> bool:
    fc_match = shutil.which("fc-match")
    if fc_match is None:
        return False
    result = subprocess.run(
        [fc_match, "--format", "%{family}\n", FONT_FAMILY],
        check=False,
        capture_output=True,
        text=True,
    )
    families = {name.strip() for line in result.stdout.splitlines() for name in line.split(",")}
    return result.returncode == 0 and FONT_FAMILY in families


def configured_variant(explicit: str | None = None) -> str:
    if explicit is not None:
        return explicit
    config_dir = os.environ.get("HERDR_PLUGIN_CONFIG_DIR")
    if not config_dir:
        return "auto"
    config_path = Path(config_dir) / "config.toml"
    if not config_path.is_file():
        return "auto"
    with config_path.open("rb") as config_file:
        variant = tomllib.load(config_file).get("variant", "auto")
    if variant not in VARIANTS:
        raise RuntimeError(f"invalid variant {variant!r} in {config_path}")
    return variant


def logo_for(agent: str, variant: str) -> str | None:
    if agent not in PUA_LOGOS or variant == "none":
        return None
    if variant == "auto":
        variant = "font" if font_available() else "text"
    return PUA_LOGOS[agent] if variant == "font" else TEXT_LOGOS[agent]


def report_logo(
    herdr: str, source: str, pane_id: str, agent: str | None, variant: str
) -> bool:
    logo = logo_for(agent, variant) if agent is not None else None
    arguments = [
        "pane",
        "report-metadata",
        pane_id,
        "--source",
        source,
    ]
    if logo is None:
        arguments.extend(("--clear-token", TOKEN_NAME))
    else:
        arguments.extend(("--token", f"{TOKEN_NAME}={logo}"))
    run_herdr(herdr, *arguments)
    return logo is not None


def event_value(value: Any, key: str) -> str | None:
    if isinstance(value, dict):
        candidate = value.get(key)
        if isinstance(candidate, str):
            return candidate
        for child in value.values():
            found = event_value(child, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = event_value(child, key)
            if found is not None:
                return found
    return None


def event_pane(raw_event: str) -> str | None:
    try:
        event = json.loads(raw_event)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid HERDR_PLUGIN_EVENT_JSON: {error}") from error
    pane_id = event_value(event, "pane_id")
    return pane_id


def current_target(herdr: str, pane_id: str) -> tuple[str, str | None]:
    response = run_herdr(herdr, "pane", "get", pane_id)
    pane = response.get("result", {}).get("pane", {})
    agent = pane.get("agent")
    return pane_id, agent if isinstance(agent, str) else None


def startup_targets(herdr: str) -> list[tuple[str, str | None]]:
    response = run_herdr(herdr, "pane", "list")
    panes = response.get("result", {}).get("panes", [])
    return [
        (pane["pane_id"], pane["agent"])
        for pane in panes
        if isinstance(pane, dict)
        and isinstance(pane.get("pane_id"), str)
        and (pane.get("agent") is None or isinstance(pane.get("agent"), str))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pane")
    parser.add_argument("--agent")
    parser.add_argument("--source")
    parser.add_argument("--variant", choices=VARIANTS)
    args = parser.parse_args()

    herdr = os.environ.get("HERDR_BIN_PATH", "herdr")
    plugin_id = os.environ.get("HERDR_PLUGIN_ID", "moneycaringcoder.agent-icons")
    source = args.source or f"plugin:{plugin_id}"
    variant = configured_variant(args.variant)

    if bool(args.pane) != bool(args.agent):
        parser.error("--pane and --agent must be supplied together")

    try:
        if args.pane and args.agent:
            targets = [(args.pane, args.agent)]
        elif os.environ.get("HERDR_PLUGIN_EVENT_JSON"):
            pane_id = event_pane(os.environ["HERDR_PLUGIN_EVENT_JSON"])
            targets = [] if pane_id is None else [current_target(herdr, pane_id)]
        else:
            targets = startup_targets(herdr)
    except (RuntimeError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return 1

    failures = []
    for pane_id, agent in targets:
        try:
            report_logo(herdr, source, pane_id, agent, variant)
        except (RuntimeError, json.JSONDecodeError) as error:
            failures.append(f"{pane_id}: {error}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
