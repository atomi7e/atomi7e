"""Sets text in Inter and turns it into outlines.

GitHub shows a README's SVGs as images, and an image cannot load fonts, so every
word is drawn as glyph outlines: the profile looks the same on any computer.
HarfBuzz places the glyphs (kerning included), fontTools gives their shapes.
Each file defines a glyph once and reuses it, which keeps the files small.
"""
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from functools import lru_cache

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FEATURES = {"kern": True, "liga": True, "calt": True}


@dataclass(frozen=True)
class Face:
    weight: int
    upem: int
    cap_height: int
    cmap: frozenset[int]
    font: hb.Font
    glyph_order: tuple[str, ...]
    outlines: dict[int, str]


@dataclass(frozen=True)
class Run:
    """A line of text drawn as glyphs. x is where its left edge ended up."""

    svg: str
    x: float
    width: float
    glyphs: frozenset[tuple[int, int]]


@lru_cache(maxsize=None)
def face(weight: int) -> Face:
    tt = TTFont(os.path.join(FONT_DIR, f"inter-latin-{weight}-normal.woff"))
    tt.flavor = None                      # HarfBuzz reads plain sfnt, not WOFF
    raw = io.BytesIO()
    tt.save(raw)
    order = tuple(tt.getGlyphOrder())
    glyph_set = tt.getGlyphSet()
    outlines = {}
    for gid, name in enumerate(order):
        pen = SVGPathPen(glyph_set, ntos=lambda v: f"{v:.0f}")
        glyph_set[name].draw(pen)
        outlines[gid] = pen.getCommands()
    return Face(weight, tt["head"].unitsPerEm, tt["OS/2"].sCapHeight, frozenset(tt.getBestCmap()),
                hb.Font(hb.Face(raw.getvalue())), order, outlines)


def printable(content: str, weight: int = 400) -> str:
    """content without the characters Inter (latin) cannot draw, such as emoji or Cyrillic.

    For text that comes from GitHub: one emoji in a description must not stop the build.
    """
    cmap = face(weight).cmap
    return " ".join("".join(ch for ch in content if ord(ch) in cmap).split())


def _shape(text: str, weight: int) -> list[tuple[int, int, int, int]]:
    """(glyph id, advance, x offset, y offset) in font units."""
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(face(weight).font, buf, FEATURES)
    glyphs = [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
              for i, p in zip(buf.glyph_infos, buf.glyph_positions)]
    if any(gid == 0 for gid, *_ in glyphs):
        raise ValueError(f"Inter (latin) has no glyph for a character in {text!r}")
    return glyphs


def _units_wide(glyphs: list[tuple[int, int, int, int]], track: float) -> float:
    return sum(adv for _, adv, _, _ in glyphs) + track * max(len(glyphs) - 1, 0)


def measure(text: str, size: float, weight: int, tracking: float = 0.0) -> float:
    """Width in pixels. tracking is in em, as CSS letter-spacing."""
    f = face(weight)
    return _units_wide(_shape(text, weight), tracking * f.upem) * size / f.upem


def cap_middle(size: float, weight: int = 400) -> float:
    """How far below the middle of a line its baseline sits: half the cap height."""
    f = face(weight)
    return f.cap_height * size / f.upem / 2


def glyph_id(weight: int, gid: int) -> str:
    return f"g{weight}-{gid}"


def text(content: str, x: float, y: float, size: float, weight: int, fill: str,
         tracking: float = 0.0, anchor: str = "start", cls: str | None = None) -> Run:
    """content set on the baseline y, starting at x (or ending at it, or centred on it)."""
    f = face(weight)
    glyphs = _shape(content, weight)
    track = tracking * f.upem
    scale = size / f.upem
    width = _units_wide(glyphs, track) * scale
    left = {"start": x, "middle": x - width / 2, "end": x - width}[anchor]

    uses, used, pen_x = [], set(), 0.0
    for gid, adv, x_off, y_off in glyphs:
        if f.outlines[gid]:                       # a space has nothing to draw
            y_attr = f' y="{y_off}"' if y_off else ""
            uses.append(f'<use href="#{glyph_id(weight, gid)}" x="{pen_x + x_off:.0f}"{y_attr}/>')
            used.add((weight, gid))
        pen_x += adv + track
    cls_attr = f' class="{cls}"' if cls else ""
    svg = (f'<g{cls_attr} fill="{fill}" transform="translate({left:.2f} {y:.2f}) '
           f'scale({scale:.6f} {-scale:.6f})">{"".join(uses)}</g>')
    return Run(svg, left, width, frozenset(used))


def fit(run: Run, room: float, what: str) -> Run:
    """The run itself, or an error when it is wider than its box: caught at build time."""
    if run.width > room + 0.01:
        raise ValueError(f"{what} is {run.width:.1f}px wide, its box has {room:.1f}px")
    return run


def wrap(content: str, size: float, weight: int, room: float) -> list[str]:
    """Greedy line breaks so that no line is wider than room."""
    lines: list[str] = []
    for word in content.split():
        candidate = f"{lines[-1]} {word}" if lines else word
        if lines and measure(candidate, size, weight) <= room:
            lines = [*lines[:-1], candidate]
        else:
            lines = [*lines, word]
    return lines


def ellipsize(content: str, size: float, weight: int, room: float) -> str:
    """content, or as much of it as fits in room followed by an ellipsis."""
    if measure(content, size, weight) <= room:
        return content
    words = content.rstrip()
    while words and measure(words.rstrip(" ,.;:") + "…", size, weight) > room:
        words = words[:-1]
    return words.rstrip(" ,.;:") + "…"


def defs(glyphs: frozenset[tuple[int, int]]) -> str:
    """One path per glyph the file uses, in font units, for the runs to point at."""
    return "".join(f'<path id="{glyph_id(w, gid)}" d="{face(w).outlines[gid]}"/>'
                   for w, gid in sorted(glyphs))
