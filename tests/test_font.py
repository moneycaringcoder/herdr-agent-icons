from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
except ImportError:  # Build-only checks run in the font virtual environment.
    TTFont = None


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(TTFont is None, "fontTools is a build-only dependency")
class FontTests(unittest.TestCase):
    def test_committed_font_contract(self) -> None:
        font = TTFont(ROOT / "dist" / "HerdrHarnessLogos-Regular.ttf")
        self.assertTrue(
            {"head", "hhea", "maxp", "OS/2", "hmtx", "cmap", "glyf", "loca", "name", "post"}.issubset(
                font.keys()
            )
        )
        self.assertFalse({"SVG ", "COLR", "CPAL", "CBDT", "fvar"}.intersection(font.keys()))
        cmap = font.getBestCmap()
        self.assertEqual(
            cmap,
            {0xE1A0: "claude", 0xE1A1: "codex", 0xE1A2: "opencode", 0xE1A3: "omp"},
        )
        self.assertEqual(font.getGlyphOrder(), [".notdef", "claude", "codex", "opencode", "omp"])
        self.assertEqual(font["post"].isFixedPitch, 1)
        for name in cmap.values():
            self.assertEqual(font["hmtx"].metrics[name][0], 600)
            self.assertGreater(font["glyf"][name].numberOfContours, 0)

    def test_build_is_deterministic(self) -> None:
        from tools.build_font import build

        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.ttf"
            second = Path(directory) / "second.ttf"
            build(first)
            build(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first.read_bytes(),
                (ROOT / "dist" / "HerdrHarnessLogos-Regular.ttf").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
