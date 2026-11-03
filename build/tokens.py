"""Edge's design tokens, as Edge's desktop prototype has them (design/prototypes/desktop/base.css).

Dark comes first, as in Edge; the light theme mirrors it. Colours with alpha stay
in rgba() form, and split_rgba() hands them to gradient stops.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# the logo's own green, the same in both themes (Edge: scripts/build_logo.py)
LOGO_TOP, LOGO_BOTTOM, LOGO_GLYPH = "#BBDC8E", "#9CC95C", "#0F180C"


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    glow: str
    glow_2: str
    tile: str
    tile_2: str
    stroke: str
    stroke_2: str
    text: str
    text_2: str
    text_3: str
    accent: str
    accent_ink: str
    accent_soft: str
    card: str
    card_edge: str
    lg_fill: str
    lg_edge_hi: str
    lg_edge_lo: str
    lg_inner: str
    thumb: str
    shadow: str
    blob_1: str
    blob_2: str
    blob_3: str


DARK = Theme(
    name="dark",
    bg="#08090a",
    glow="rgba(156,201,92,.14)",
    glow_2="rgba(100,210,255,.05)",
    tile="#1f2023",
    tile_2="#2a2b2f",
    stroke="rgba(255,255,255,.07)",
    stroke_2="rgba(255,255,255,.12)",
    text="#f5f5f7",
    text_2="#a1a1a6",
    text_3="#8a8a90",
    accent="#9cc95c",
    accent_ink="#bbdc8e",
    accent_soft="rgba(156,201,92,.16)",
    card="rgba(19,20,22,.80)",
    card_edge="rgba(255,255,255,.16)",
    lg_fill="rgba(22,24,26,.30)",
    lg_edge_hi="rgba(255,255,255,.62)",
    lg_edge_lo="rgba(255,255,255,.10)",
    lg_inner="rgba(255,255,255,.13)",
    thumb="rgba(255,255,255,.13)",
    shadow="rgba(0,0,0,.55)",
    blob_1="rgba(156,201,92,.40)",
    blob_2="rgba(56,182,196,.26)",
    blob_3="rgba(214,226,110,.16)",
)

LIGHT = Theme(
    name="light",
    bg="#f2f2f7",
    glow="rgba(127,179,66,.2)",
    glow_2="rgba(0,113,227,.06)",
    tile="#f4f4f7",
    tile_2="#e6e6eb",
    stroke="rgba(0,0,0,.07)",
    stroke_2="rgba(0,0,0,.12)",
    text="#1d1d1f",
    text_2="#5c5c62",
    text_3="#6e6e73",
    accent="#7fb342",
    accent_ink="#44701a",
    accent_soft="rgba(127,179,66,.17)",
    card="rgba(255,255,255,.84)",
    card_edge="rgba(255,255,255,1)",
    lg_fill="rgba(255,255,255,.40)",
    lg_edge_hi="rgba(255,255,255,1)",
    lg_edge_lo="rgba(255,255,255,.4)",
    lg_inner="rgba(255,255,255,.7)",
    thumb="rgba(255,255,255,.85)",
    shadow="rgba(30,40,20,.3)",
    blob_1="rgba(127,179,66,.45)",
    blob_2="rgba(0,150,200,.22)",
    blob_3="rgba(240,196,80,.24)",
)

THEMES = (DARK, LIGHT)

_RGBA = re.compile(r"rgba\((\d+),(\d+),(\d+),([\d.]+)\)")


def split_rgba(colour: str) -> tuple[str, float]:
    """rgba(r,g,b,a) as ("rgb(r,g,b)", a); any other colour is opaque.

    SVG gradients fade colour and opacity separately, so a stop must keep its
    colour and drop only its opacity, or the fade turns grey on the way out.
    """
    m = _RGBA.fullmatch(colour)
    if not m:
        return colour, 1.0
    r, g, b, a = m.groups()
    return f"rgb({r},{g},{b})", float(a)
