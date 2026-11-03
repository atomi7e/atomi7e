"""Pieces the scenes share: layers that remember their glyphs, chips, labels and the file itself."""
from __future__ import annotations

import html
from dataclasses import dataclass

import shapes as sh
import typeset as ty
from tokens import Theme

W = 840            # GitHub's README column on a computer is about this wide
# Between the pictures GitHub leaves a paragraph's 16px plus the ~5.6px an inline image
# keeps under its baseline; the about row splits on about the same, so the grid reads even.
GAP = 21.5
PAD = 36
R_CARD, R_TILE, R_CHIP = 28, 20, 8

# light that drifts behind the glass (Edge: .blob, a little quicker for a page seen briefly)
MOTION = (
    ".blob{transform-box:fill-box;transform-origin:center;animation:drift 24s ease-in-out infinite alternate}"
    ".b2{animation-duration:30s;animation-direction:alternate-reverse}.b3{animation-duration:27s}"
    "@keyframes drift{0%{transform:translate(0,0) scale(1)}50%{transform:translate(6%,8%) scale(1.08)}"
    "100%{transform:translate(-4%,3%) scale(.96)}}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)
SPRING = "cubic-bezier(.2,.9,.25,1.12)"     # Edge's --spring
OUT = "cubic-bezier(.33,1,.68,1)"           # Edge's --out3

Blobs = tuple[tuple[float, float, float], ...]


@dataclass(frozen=True)
class Layer:
    svg: str = ""
    glyphs: frozenset[tuple[int, int]] = frozenset()


@dataclass(frozen=True)
class Scene:
    width: float
    height: float
    title: str
    desc: str
    css: str
    defs: str
    body: Layer


def lay(*items: Layer | ty.Run | str) -> Layer:
    """Joins pieces in drawing order and keeps track of the glyphs they use."""
    svg = "".join(i if isinstance(i, str) else i.svg for i in items)
    glyphs = frozenset().union(*(i.glyphs for i in items if not isinstance(i, str)))
    return Layer(svg, glyphs)


def render(scene: Scene, theme: Theme) -> str:
    defs = sh.common_defs(theme) + scene.defs + ty.defs(scene.body.glyphs)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene.width:g}" height="{scene.height:g}" '
            f'viewBox="0 0 {scene.width:g} {scene.height:g}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{html.escape(scene.title)}</title><desc id="desc">{html.escape(scene.desc)}</desc>'
            f'<style>{MOTION}{scene.css}</style><defs>{defs}</defs>{scene.body.svg}</svg>\n')


def clip_def(cid: str, w: float, h: float) -> str:
    return f'<clipPath id="{cid}">{sh.rect_shape(0, 0, w, h, R_CARD)("")}</clipPath>'


def card_ground(cid: str, w: float, h: float, t: Theme, blobs: Blobs, glow_at: tuple[float, float]) -> str:
    """The drifting light under a calm card, cut to the card's corners.

    In Edge a shadow sets a card off the page; a picture cannot draw outside itself,
    so a hairline does it, which a light card on GitHub's white page needs.
    """
    rim = sh.rect_shape(.5, .5, w - 1, h - 1, R_CARD - .5)(sh.attrs(fill="none", stroke=t.stroke))
    return (f'<g clip-path="url(#{cid})">{sh.ambient(w, h, t, blobs, glow_at)}'
            f'{sh.card(sh.rect_shape(0, 0, w, h, R_CARD), t)}</g>{rim}')


def micro(label: str, x: float, y: float, t: Theme) -> ty.Run:
    """Edge's Micro style: 11, uppercase, spaced out, quiet."""
    return ty.text(label.upper(), x, y, 11, 600, t.text_3, tracking=0.08)


def chip(x: float, y: float, label: str, t: Theme, icon: str | None = None) -> tuple[Layer, float]:
    """A tile-coloured chip, 30 high; returns it and its width."""
    h, pad, size = 30, 11, 14
    text_x = x + pad + (size + 6 if icon else 0)
    run = ty.text(label, text_x, y + h / 2 + ty.cap_middle(13, 500), 13, 500, t.text)
    w = text_x - x + run.width + pad
    glyph = sh.icon(icon, x + pad, y + (h - size) / 2, size, t.text_2) if icon else ""
    return lay(sh.tile(sh.rect_shape(x, y, w, h, R_CHIP), t), glyph, run), w


def chip_row(x: float, y: float, labels: tuple[tuple[str | None, str], ...], room: float,
             t: Theme, gap: float = 8, line: float = 38) -> tuple[Layer, float]:
    """Chips that wrap to a new line when they run out of room; returns them and their bottom."""
    pieces, cx, cy = [], x, y
    for icon, label in labels:
        _, w = chip(0, 0, label, t, icon)
        if w > room:
            raise ValueError(f"chip {label!r} is {w:.1f}px wide, the row has {room:.1f}px")
        if cx > x and cx + w > x + room:
            cx, cy = x, cy + line
        piece, w = chip(cx, cy, label, t, icon)
        pieces.append(piece)
        cx += w + gap
    return lay(*pieces), cy + 30
