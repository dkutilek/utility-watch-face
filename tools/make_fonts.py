#!/usr/bin/env python3
"""Builds the two bundled fonts from Google Sans Flex (SIL Open Font License 1.1).

The variable font is fixed to one weight per use and cut down to Latin characters,
which keeps the watch face small. The results are committed, so this only needs
rerunning to change a weight. Requires fontTools.

    python3 tools/make_fonts.py path/to/GoogleSansFlex[ROND,opsz,slnt,wdth,wght].ttf

Source: https://github.com/google/fonts/tree/main/ofl/googlesansflex
"""
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).resolve().parent.parent / "res" / "font"

# Axis values chosen by matching against a Pixel Watch 3 screenshot of the Utility face.
# Like Utility, the time draws lighter on the always-on display. Screenshots can't capture
# that mode on a real watch, so its weight was set by eye rather than measured.
TIME_FONTS = ("face_time", "face_time_ambient")
INSTANCES = {
    "face_time": {"wght": 425, "opsz": 144, "wdth": 100, "ROND": 0, "slnt": 0},
    "face_time_ambient": {"wght": 300, "opsz": 144, "wdth": 100, "ROND": 0, "slnt": 0},
    "face_text": {"wght": 625, "opsz": 18, "wdth": 100, "ROND": 0, "slnt": 0},
}
LATIN = list(range(0x20, 0x7F)) + list(range(0xA0, 0x100))

# Google Sans Flex centers its colon on lowercase letters. Utility's clock font centers a
# smaller colon on the digits, so the time font gets a reshaped one: scaled to 76% (the
# measured ratio of dot sizes) and raised to sit just below the middle of the digits.
COLON_SCALE = 0.76
COLON_CENTER_OVER_DIGITS = 0.02  # fraction of digit height; tuned against the Pixel Watch 3


def colon_glyph_names(font):
    names = {font.getBestCmap()[ord(":")]}
    for lookup in font["GSUB"].table.LookupList.Lookup:
        for table in lookup.SubTable:
            for src, dst in getattr(table, "mapping", {}).items():
                if src in names:
                    names.add(dst)
    return names


def reshape_colon(font):
    glyf, hmtx = font["glyf"], font["hmtx"]
    two = glyf[font.getBestCmap()[ord("2")]]
    two.recalcBounds(glyf)
    digit_center = (two.yMin + two.yMax) / 2 - COLON_CENTER_OVER_DIGITS * (two.yMax - two.yMin)
    names = colon_glyph_names(font)
    outlines = {name for name in names if not glyf[name].isComposite()}
    for name in outlines:
        glyph = glyf[name]
        glyph.recalcBounds(glyf)
        cx, cy = (glyph.xMin + glyph.xMax) / 2, (glyph.yMin + glyph.yMax) / 2
        trimmed = round((1 - COLON_SCALE) * (glyph.xMax - glyph.xMin))
        coords = glyph.coordinates
        for i, (x, y) in enumerate(coords):
            coords[i] = (round(cx + (x - cx) * COLON_SCALE - trimmed / 2),
                         round(digit_center + (y - cy) * COLON_SCALE))
        glyph.recalcBounds(glyf)
        advance, _ = hmtx[name]
        hmtx[name] = (advance - trimmed, glyph.xMin)
    # Variants such as colon.time reuse the colon raised by an offset. It is centered now,
    # so drop the vertical offset and keep the horizontal one.
    for name in names - outlines:
        glyph = glyf[name]
        for component in glyph.components:
            if component.glyphName in outlines:
                component.y = 0
        glyph.recalcBounds(glyf)
        hmtx[name] = (hmtx[name][0], glyph.xMin)


def main(source):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, axes in INSTANCES.items():
        font = instantiateVariableFont(TTFont(source), axes)
        if name in TIME_FONTS:
            reshape_colon(font)
        options = subset.Options()
        options.layout_features = ["kern", "liga", "calt", "tnum", "lnum"]
        subsetter = subset.Subsetter(options)
        subsetter.populate(unicodes=LATIN)
        subsetter.subset(font)
        font.save(OUT / f"{name}.ttf")
        print(f"{name}.ttf: {(OUT / f'{name}.ttf').stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1])
