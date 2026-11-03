"""Edge's surfaces in SVG: the drifting light, calm cards, liquid glass, the logo and icons.

An SVG shown as an image has no backdrop-filter, so the glass is built the way
Edge's CSS layers it: a thin fill, a soft inner light at top and bottom, a rim
that is brightest at the corners, and a shadow underneath. The light behind it
is already soft, which stands in for the blur.
"""
from __future__ import annotations

import math
from typing import Callable

from tokens import LOGO_BOTTOM, LOGO_GLYPH, LOGO_TOP, Theme, split_rgba

Shape = Callable[[str], str]      # takes extra attributes, returns the element

# the Edge sign, drawn on a 1024 grid (Edge: design/logo/edge-mark.svg)
EDGE_MARK = (
    "M125.0 420.2A339 339 0 0 1 553.9 192.2L452.6 246.0A269 269 0 0 0 226.3 366.4Z",
    "M251.1 789.2A339 339 0 0 0 789.3 503.0L718.3 540.8A269 269 0 0 1 322.2 751.4Z",
    "M551.2 191.3A339 339 0 0 1 596.6 209.1L513.3 253.4A269 269 0 0 0 448.4 246.0Z",
    "M785.8 465.2A339 339 0 0 1 789.4 505.3L718.0 543.2A269 269 0 0 0 719.1 500.7Z",
    "M115.6 462.6L594.4 208.0A339 339 0 0 1 649.9 240.8L111.7 527.0A339 339 0 0 1 115.6 462.6Z",
    "M114.9 562.6L677.7 263.4A339 339 0 0 1 716.6 305.0L127.6 618.2A339 339 0 0 1 114.9 562.6Z",
    "M139.3 649.3L735.9 332.1A339 339 0 0 1 761.7 380.7L165.1 697.9A339 339 0 0 1 139.3 649.3Z",
    "M184.4 725.0L773.4 411.8A339 339 0 0 1 786.1 467.4L223.3 766.6A339 339 0 0 1 184.4 725.0Z",
    "M702.5 349.9L826.1 284.2L851.9 332.7L728.3 398.4ZM787.9 233.7L967.9 239.9L872.4 392.6Z",
)

# Lucide icons on their 24 grid (lucide-static 0.460.0, ISC licence)
ICONS = {
    "notebook-pen": '<path d="M13.4 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7.4"/>'
                    '<path d="M2 6h4M2 10h4M2 14h4M2 18h4"/>'
                    '<path d="M21.378 5.626a1 1 0 1 0-3.004-3.004l-5.01 5.012a2 2 0 0 0-.506.854'
                    'l-.837 2.87a.5.5 0 0 0 .62.62l2.87-.837a2 2 0 0 0 .854-.506z"/>',
    "calendar-days": '<path d="M8 2v4M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/>'
                     '<path d="M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/>',
    "square-kanban": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M8 7v7M12 7v4M16 7v9"/>',
    "circle-check-big": '<path d="M21.801 10A10 10 0 1 1 17 3.335"/><path d="m9 11 3 3L22 4"/>',
    "wallet": '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3'
              'a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "monitor": '<rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>'
             '<path d="M2 12h20"/>',
    "smartphone": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/>',
    "arrow-up-right": '<path d="M7 7h10v10M7 17 17 7"/>',
}


def attrs(**kw: object) -> str:
    """Keyword arguments as SVG attributes: stroke_width becomes stroke-width, None is left out."""
    return "".join(f' {k.rstrip("_").replace("_", "-")}="{v}"' for k, v in kw.items() if v is not None)


def stop(offset: float, colour: str, fade: float = 1.0) -> str:
    rgb, alpha = split_rgba(colour)
    return f'<stop offset="{offset:g}" stop-color="{rgb}" stop-opacity="{alpha * fade:.3g}"/>'


def common_defs(theme: Theme) -> str:
    """Gradients and filters every scene shares; bounding-box units fit them to any shape."""
    t = theme
    return (
        # the glass rim, brighter in the corners the light comes from (CSS: 140deg)
        f'<linearGradient id="lg-edge" x1="0" y1="0" x2="1" y2="1">{stop(0, t.lg_edge_hi)}'
        f'{stop(.26, t.lg_edge_lo)}{stop(.48, t.lg_edge_lo, 0)}{stop(.58, t.lg_edge_lo, 0)}'
        f'{stop(.76, t.lg_edge_lo)}{stop(1, t.lg_edge_hi)}</linearGradient>'
        # the light inside the glass, under its top and bottom edges
        f'<linearGradient id="lg-inner" x1="0" y1="0" x2="0" y2="1">{stop(0, t.lg_inner)}'
        f'{stop(.32, t.lg_inner, 0)}{stop(.72, t.lg_inner, 0)}{stop(1, t.lg_inner, .7)}</linearGradient>'
        # the calm card's rim (CSS: 160deg, at .55)
        f'<linearGradient id="card-edge" x1="0" y1="0" x2=".36" y2="1">{stop(0, t.card_edge)}'
        f'{stop(.3, t.card_edge, 0)}{stop(.8, t.card_edge, 0)}{stop(1, t.card_edge)}</linearGradient>'
        f'<linearGradient id="logo" x1="0" y1="0" x2="0" y2="1">{stop(0, LOGO_TOP)}{stop(1, LOGO_BOTTOM)}'
        f'</linearGradient>'
        # on the sign itself the gradient spans its whole 1024 grid, or every stripe would restart it
        f'<linearGradient id="logo-mark" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="1024">'
        f'{stop(0, LOGO_TOP)}{stop(1, LOGO_BOTTOM)}</linearGradient>'
        f'<radialGradient id="glow">{stop(0, t.glow)}{stop(.62, t.glow, 0)}</radialGradient>'
        f'<radialGradient id="glow-2">{stop(0, t.glow_2)}{stop(.6, t.glow_2, 0)}</radialGradient>'
        + "".join(f'<radialGradient id="blob-{i}">{stop(0, c)}{stop(1, c, 0)}</radialGradient>'
                  for i, c in enumerate((t.blob_1, t.blob_2, t.blob_3), start=1))
        # room for the whole blur below a pill only 32 high, or its edge shows as a box
        + '<filter id="soft" x="-60%" y="-200%" width="220%" height="500%">'
          '<feGaussianBlur stdDeviation="14"/></filter>'
          # in the sign's own 1024 units: about 13px on a 150px sign
          '<filter id="halo" x="-50%" y="-50%" width="200%" height="200%">'
          '<feGaussianBlur stdDeviation="90"/></filter>'
    )


def rect_shape(x: float, y: float, w: float, h: float, r: float) -> Shape:
    return lambda extra="": f'<rect{attrs(x=f"{x:g}", y=f"{y:g}", width=f"{w:g}", height=f"{h:g}", rx=f"{r:g}")}{extra}/>'


def squircle_d(x: float, y: float, size: float, n: float = 5.0, steps: int = 128) -> str:
    """The continuous-corner tile of Apple icons, as a superellipse (as Edge's logo script)."""
    half = size / 2
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        c, s = math.cos(t), math.sin(t)
        px = x + half + half * math.copysign(abs(c) ** (2 / n), c)
        py = y + half + half * math.copysign(abs(s) ** (2 / n), s)
        pts.append(f"{px:.1f} {py:.1f}")
    return "M" + "L".join(pts) + "Z"


def squircle_shape(x: float, y: float, size: float) -> Shape:
    d = squircle_d(x, y, size)
    return lambda extra="": f'<path d="{d}"{extra}/>'


def ambient(w: float, h: float, theme: Theme, blobs: tuple[tuple[float, float, float], ...],
            glow_at: tuple[float, float] = (0.06, -0.12)) -> str:
    """Edge's ground: near black (or soft grey), a glow in the corner and light that drifts.

    blobs are (cx, cy, r) for blob-1..3; the drift animation lives in the scene's CSS.
    """
    gx, gy = glow_at
    parts = [f'<rect width="{w:g}" height="{h:g}" fill="{theme.bg}"/>',
             f'<ellipse cx="{gx * w:.0f}" cy="{gy * h:.0f}" rx="{w * .64:.0f}" ry="{w * .44:.0f}" '
             f'fill="url(#glow)" opacity=".5"/>',
             f'<ellipse cx="{w * 1.04:.0f}" cy="{h * -.06:.0f}" rx="{w * .54:.0f}" ry="{w * .37:.0f}" '
             f'fill="url(#glow-2)" opacity=".5"/>']
    parts += [f'<circle class="blob b{i}" cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="url(#blob-{i})"/>'
              for i, (cx, cy, r) in enumerate(blobs, start=1)]
    return "".join(parts)


def glass(shape: Shape, theme: Theme, shadow: bool = True) -> str:
    """Liquid glass: for what is controlled and floats over the content."""
    parts = []
    if shadow:
        parts.append(f'<g transform="translate(0 12)" opacity=".8">'
                     f'{shape(attrs(fill=theme.shadow, filter="url(#soft)"))}</g>')
    parts += [shape(attrs(fill=theme.lg_fill)),
              shape(attrs(fill="url(#lg-inner)")),
              shape(attrs(fill="none", stroke="url(#lg-edge)", stroke_width="1.25"))]
    return "".join(parts)


def card(shape: Shape, theme: Theme) -> str:
    """A calm card for what is read: dense fill and a thin light rim."""
    return (shape(attrs(fill=theme.card))
            + shape(attrs(fill="none", stroke="url(#card-edge)", stroke_width="1.25", opacity=".55")))


def tile(shape: Shape, theme: Theme) -> str:
    """A tile or chip inside a card."""
    return shape(attrs(fill=theme.tile, stroke=theme.stroke, stroke_width="1"))


def edge_mark(x: float, y: float, size: float, fill: str, extra: str = "") -> str:
    paths = "".join(f'<path d="{d}"/>' for d in EDGE_MARK)
    return f'<g transform="translate({x:g} {y:g}) scale({size / 1024:.5f})" fill="{fill}"{extra}>{paths}</g>'


def app_icon(x: float, y: float, size: float) -> str:
    """Edge's icon: the green squircle with the dark sign."""
    return squircle_shape(x, y, size)(attrs(fill="url(#logo)")) + edge_mark(x, y, size, LOGO_GLYPH)


def icon(name: str, x: float, y: float, size: float, colour: str, width: float = 2.0) -> str:
    return (f'<g transform="translate({x:g} {y:g}) scale({size / 24:.4f})" fill="none" stroke="{colour}" '
            f'stroke-width="{width:g}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')
