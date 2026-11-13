#!/usr/bin/env python3
"""Regenerate Romanian-only variable WOFF2s; optional, not part of the site build.

Run with: uv run --no-project --with 'fonttools[woff]==4.68.0' python scripts/subset_fonts.py
The original Latin and Latin-ext files remain unchanged and retain full coverage.
"""
from pathlib import Path

from fontTools import subset
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"
ROMANIAN = set(range(0x0102, 0x0104)) | set(range(0x015E, 0x0160)) | \
    set(range(0x0162, 0x0164)) | set(range(0x0218, 0x021C))


def verify(original, optimized):
    """Confirm coverage, variable axes, metrics and outlines across used weights."""
    assert set(optimized.getBestCmap()) == ROMANIAN, "Unexpected subset coverage"
    axes = [(axis.axisTag, axis.minValue, axis.defaultValue, axis.maxValue)
            for axis in original["fvar"].axes]
    assert axes == [(axis.axisTag, axis.minValue, axis.defaultValue, axis.maxValue)
                    for axis in optimized["fvar"].axes], "Variable axes changed"
    assert original["head"].unitsPerEm == optimized["head"].unitsPerEm
    for table, fields in {
        "hhea": ("ascent", "descent", "lineGap"),
        "OS/2": ("sTypoAscender", "sTypoDescender", "sTypoLineGap",
                 "usWinAscent", "usWinDescent", "sxHeight", "sCapHeight"),
    }.items():
        for field in fields:
            assert getattr(original[table], field) == getattr(optimized[table], field)
    weight_axis = next(axis for axis in original["fvar"].axes if axis.axisTag == "wght")
    weights = {weight_axis.minValue, weight_axis.defaultValue, weight_axis.maxValue,
               400, 500, 600, 650, 700, 750, 800}
    for weight in sorted(weights):
        if not weight_axis.minValue <= weight <= weight_axis.maxValue:
            continue
        original_glyphs = original.getGlyphSet(location={"wght": weight})
        optimized_glyphs = optimized.getGlyphSet(location={"wght": weight})
        for codepoint in sorted(ROMANIAN):
            names = (original.getBestCmap()[codepoint], optimized.getBestCmap()[codepoint])
            recordings = []
            widths = []
            for glyphs, name in zip((original_glyphs, optimized_glyphs), names):
                pen = DecomposingRecordingPen(glyphs)
                glyphs[name].draw(pen)
                recordings.append(pen.value)
                widths.append(glyphs[name].width)
            assert widths[0] == widths[1], f"Advance changed: U+{codepoint:04X}, {weight}"
            assert recordings[0] == recordings[1], f"Outline changed: U+{codepoint:04X}, {weight}"


def main():
    for family in ("dm-sans", "manrope"):
        source = FONT_DIR / f"{family}-latin-ext.woff2"
        destination = FONT_DIR / f"{family}-romanian.woff2"
        font = TTFont(source, recalcTimestamp=False)
        options = subset.Options()
        options.flavor = "woff2"
        options.name_IDs = ["*"]
        options.name_languages = ["*"]
        options.name_legacy = True
        options.layout_features = ["*"]
        options.notdef_outline = True
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(unicodes=ROMANIAN)
        subsetter.subset(font)
        font.save(destination)
        with TTFont(source) as original, TTFont(destination) as optimized:
            verify(original, optimized)
        print(f"{source.name}: {source.stat().st_size:,} → "
              f"{destination.name}: {destination.stat().st_size:,} bytes; "
              "coverage, axes, metrics and outlines verified")


if __name__ == "__main__":
    main()
