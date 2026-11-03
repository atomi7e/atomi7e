"""The profile's three pictures: the hero, the Edge card and the row about me.

Laid out like Edge's dashboard: one large tile, the rest smaller. Glass only on
what floats (the handle, the tabs, the sign, the link); calm cards hold the rest.
"""
from __future__ import annotations

import kit
import shapes as sh
import typeset as ty
from kit import GAP, OUT, PAD, R_CARD, R_TILE, SPRING, W, Layer, Scene, lay
from tokens import Theme

NAME = "Artyom Legezin"
HANDLE = "@atomi7e"
TAGLINE = "Student at AITU · trader · building my own tools"

TABS = ("Study", "Trade", "Build")          # in the order of the tagline
TAB_W, TAB_H, TAB_IN, TAB_PERIOD = 92, 40, 4, 9

EDGE_TAGLINE = "A personal app for one trader"
EDGE_ABOUT = ("Trading journal, calendar, notes, habits and money in one place. "
              "One set of data on Windows, the web and iPhone.")
PLATFORMS = (("monitor", "Windows"), ("globe", "Web"), ("smartphone", "iPhone"))
MODULES = (("calendar-days", "Calendar", "Google Calendar"),
           ("square-kanban", "Notes & Kanban", "Boards and notes"),
           ("circle-check-big", "Habits", "Daily streaks"),
           ("wallet", "Money", "Wallets, budgets"))
# an illustration of a journal's curve, not real results: no axes, no numbers
SPARK = (.20, .24, .21, .30, .28, .36, .33, .29, .40, .44, .41, .50, .47, .56, .62, .57, .66, .71, .68, .79, .88)

NOW = (("Studying at AITU", "Astana IT University"),
       ("Building Edge", "For Windows, the web and iPhone"),
       ("Trading", "And journaling every trade"))
MAIN_STACK = ("Python", "Swift", "TypeScript")
MORE_STACK = ("JavaScript", "Django", "Docker", "HTML & CSS", "Git")


# ---------------------------------------------------------------- hero

def handle(x: float, y: float, t: Theme) -> Layer:
    """The @handle in a glass pill, with Edge's green status dot."""
    h = 32
    run = ty.text(HANDLE, x + 28, y + h / 2 + ty.cap_middle(14, 500), 14, 500, t.text)
    pill = sh.rect_shape(x, y, 28 + run.width + 14, h, h / 2)
    dot = (f'<circle cx="{x + 16:g}" cy="{y + h / 2:g}" r="7" fill="{t.accent_soft}"/>'
           f'<circle cx="{x + 16:g}" cy="{y + h / 2:g}" r="3.5" fill="{t.accent}"/>')
    return lay(sh.glass(pill, t), dot, run)


def tabs(x: float, y: float, t: Theme) -> Layer:
    """Edge's period switch: a light drop of glass slides under the labels, the chosen one turns green."""
    n = len(TABS)
    drop_h = TAB_H - 2 * TAB_IN
    track = sh.rect_shape(x, y, n * TAB_W + 2 * TAB_IN, TAB_H, TAB_H / 2)
    drop = sh.rect_shape(x + TAB_IN, y + TAB_IN, TAB_W, drop_h, drop_h / 2)
    baseline = y + TAB_H / 2 + ty.cap_middle(15, 500)
    labels = [ty.fit(ty.text(label, x + TAB_IN + TAB_W * (i + .5), baseline, 15, 500,
                             t.accent_ink if i == 0 else t.text_2, anchor="middle", cls=f"tab{i}"),
                     TAB_W - 16, f"tab {label}")
              for i, label in enumerate(TABS)]
    return lay(sh.glass(track, t), '<g class="drop">', drop(sh.attrs(fill=t.thumb)),
               drop(sh.attrs(fill="none", stroke="url(#lg-edge)", stroke_width="1", opacity=".7")), "</g>",
               *labels)


def tabs_css(t: Theme) -> str:
    """The drop hops from tab to tab every three seconds and stretches only while it moves."""
    s = TAB_W
    hop = (f"0%,30%{{transform:translateX(0)}}31.6%{{transform:translateX({s / 2:g}px) scaleX(1.16)}}"
           f"33.3%,63.3%{{transform:translateX({s:g}px)}}64.9%{{transform:translateX({1.5 * s:g}px) scaleX(1.16)}}"
           f"66.6%,96.6%{{transform:translateX({2 * s:g}px)}}98.3%{{transform:translateX({s:g}px) scaleX(1.16)}}"
           f"100%{{transform:translateX(0)}}")
    on, off = t.accent_ink, t.text_2
    lit = ("0%,30%{{fill:{a}}}33.3%,96.6%{{fill:{b}}}100%{{fill:{a}}}",
           "0%,30%{{fill:{b}}}33.3%,63.3%{{fill:{a}}}66.6%,100%{{fill:{b}}}",
           "0%,63.3%{{fill:{b}}}66.6%,96.6%{{fill:{a}}}100%{{fill:{b}}}")
    return (f".drop{{transform-box:fill-box;transform-origin:center;animation:hop {TAB_PERIOD}s {SPRING} infinite}}"
            f"@keyframes hop{{{hop}}}"
            + "".join(f".tab{i}{{animation:lit{i} {TAB_PERIOD}s ease infinite}}"
                      f"@keyframes lit{i}{{{frames.format(a=on, b=off)}}}" for i, frames in enumerate(lit)))


def lens(x: float, y: float, size: float, t: Theme) -> str:
    """Edge's sign floating in a glass squircle, with a soft green glow under it."""
    tile = sh.squircle_shape(x, y, size)
    return ('<g class="float">' + sh.glass(tile, t)
            + sh.edge_mark(x, y, size, t.accent, ' filter="url(#halo)" opacity=".5"')
            + sh.edge_mark(x, y, size, "url(#logo-mark)") + "</g>")


def hero(t: Theme) -> Scene:
    w, h, left, icon = W, 312, 44, 150
    room = w - 2 * left - icon - 32
    ground = f'<g clip-path="url(#hero-clip)">{sh.ambient(w, h, t, ((120, 30, 300), (730, 210, 250), (430, 380, 230)))}</g>'
    rim = sh.rect_shape(.5, .5, w - 1, h - 1, R_CARD)(sh.attrs(fill="none", stroke=t.stroke_2))
    body = lay(ground, rim, handle(left, 44, t),
               ty.fit(ty.text(NAME, left, 160, 58, 600, t.text, tracking=-0.025), room, "name"),
               ty.fit(ty.text(TAGLINE, left, 198, 19, 400, t.text_2), room, "tagline"),
               tabs(left, 228, t), lens(w - left - icon, (h - icon) / 2, icon, t))
    css = tabs_css(t) + (".float{animation:float 7s ease-in-out infinite alternate}"
                         "@keyframes float{from{transform:translateY(-5px)}to{transform:translateY(5px)}}")
    return Scene(w, h, f"{NAME} ({HANDLE})", TAGLINE, css, kit.clip_def("hero-clip", w, h), body)


# ---------------------------------------------------------------- Edge

def open_pill(right: float, y: float, t: Theme) -> Layer:
    """A glass button that says where the picture links to."""
    h, pad, size, label = 32, 14, 14, "Open page"
    label_w = ty.measure(label, 13, 500)
    w = pad + label_w + 6 + size + 12
    x = right - w
    run = ty.text(label, x + pad, y + h / 2 + ty.cap_middle(13, 500), 13, 500, t.accent_ink)
    arrow = sh.icon("arrow-up-right", x + pad + label_w + 6, y + (h - size) / 2, size, t.accent_ink)
    return lay(sh.glass(sh.rect_shape(x, y, w, h, h / 2), t), run, arrow)


def edge_story(x: float, y: float, room: float, t: Theme) -> Layer:
    baseline = y + 112
    title = ty.text("Edge", x, baseline, 34, 600, t.text, tracking=-0.02)
    # the chip's middle sits on the middle of the title's capitals
    private, _ = kit.chip(x + title.width + 14, baseline - ty.cap_middle(34, 600) - 15, "Private code", t, "lock")
    lines = ty.wrap(EDGE_ABOUT, 15, 400, room)
    about = [ty.text(line, x, y + 178 + i * 23, 15, 400, t.text_2) for i, line in enumerate(lines)]
    platforms, bottom = kit.chip_row(x, y + 270, PLATFORMS, room, t)
    if len(lines) > 3 or bottom > y + 300:
        raise ValueError("the Edge story does not fit its column")
    return lay(sh.app_icon(x, y, 64), open_pill(x + room, y + 16, t), title, private,
               ty.fit(ty.text(EDGE_TAGLINE, x, y + 144, 18, 500, t.text), room, "Edge tagline"),
               *about, platforms)


def smooth(points: list[tuple[float, float]]) -> str:
    """A curve through the points (Catmull-Rom as cubic Béziers)."""
    d = [f"M{points[0][0]:.1f} {points[0][1]:.1f}"]
    for i in range(len(points) - 1):
        p0, p1, p2 = points[max(i - 1, 0)], points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return "".join(d)


def spark(x: float, y: float, w: float, h: float, t: Theme) -> str:
    """The journal's curve draws itself, then the area under it and the end dot fade in."""
    points = [(x + w * i / (len(SPARK) - 1), y + h - v * h) for i, v in enumerate(SPARK)]
    line = smooth(points)
    ex, ey = points[-1]
    grid = "".join(f'<path d="M{x:g} {y + h * f:.1f}H{x + w:g}" stroke="{t.stroke_2}" stroke-dasharray="2 6"/>'
                   for f in (.3, .65, 1))
    return (grid + f'<path class="area" d="{line}L{x + w:.1f} {y + h:.1f}L{x:.1f} {y + h:.1f}Z" fill="url(#spark-fill)"/>'
            f'<path class="line" d="{line}" pathLength="1" fill="none" stroke="{t.accent}" stroke-width="2.25" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<g class="end"><circle cx="{ex:.1f}" cy="{ey:.1f}" r="8" fill="{t.accent_soft}"/>'
            f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="3.5" fill="{t.accent}"/></g>')


def journal(x: float, y: float, w: float, h: float, t: Theme) -> Layer:
    baseline = y + 27 + ty.cap_middle(15, 600)
    label = ty.text("Trading journal", x + 46, baseline, 15, 600, t.text)
    note = ty.text("Trades, plans and notes", x + w - 18, baseline, 13, 400, t.text_3, anchor="end")
    ty.fit(note, w - 46 - label.width - 18 - 16, "journal note")
    return lay(sh.tile(sh.rect_shape(x, y, w, h, R_TILE), t), sh.icon("notebook-pen", x + 18, y + 18, 18, t.accent_ink),
               label, note, spark(x + 18, y + 56, w - 36, h - 56 - 20, t))


def module(x: float, y: float, w: float, h: float, item: tuple[str, str, str], t: Theme) -> Layer:
    icon, label, note = item
    room = w - 44 - 12
    return lay(sh.tile(sh.rect_shape(x, y, w, h, R_TILE), t), sh.icon(icon, x + 16, y + (h - 18) / 2, 18, t.accent_ink),
               ty.fit(ty.text(label, x + 44, y + 30, 14, 600, t.text), room, label),
               ty.fit(ty.text(note, x + 44, y + 49, 12, 400, t.text_3), room, note))


def modules(x: float, y: float, w: float, t: Theme) -> Layer:
    tw, th, gap = (w - 12) / 2, 68, 12
    return lay(*(module(x + (i % 2) * (tw + gap), y + (i // 2) * (th + gap), tw, th, item, t)
                 for i, item in enumerate(MODULES)))


def edge(t: Theme) -> Scene:
    w, h, left_w = W, 372, 372
    right_x = PAD + left_w + 36
    right_w = w - PAD - right_x
    ground = kit.card_ground("edge-clip", w, h, t, ((90, 400, 260), (800, 30, 220), (470, -30, 190)), (.92, -.1))
    body = lay(ground, edge_story(PAD, PAD, left_w, t),
               journal(right_x, PAD, right_w, 140, t), modules(right_x, PAD + 152, right_w, t))
    css = (f".line{{stroke-dasharray:1;animation:draw 2.4s {OUT} .4s both}}"
           "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
           ".area{animation:rise 1.4s ease-out 1.4s both}.end{animation:rise .5s ease-out 2.6s both}"
           "@keyframes rise{from{opacity:0}}")
    defs = (kit.clip_def("edge-clip", w, h) + '<linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">'
            f'{sh.stop(0, t.accent, .28)}{sh.stop(1, t.accent, 0)}</linearGradient>')
    desc = f"Edge, {EDGE_TAGLINE.lower()}. {EDGE_ABOUT} The code is private."
    return Scene(w, h, "Edge", desc, css, defs, body)


# ---------------------------------------------------------------- about

def now_card(w: float, t: Theme) -> Layer:
    x, room = 28, w - 28 - 22 - 28
    items: list[Layer | ty.Run | str] = []
    for i, (title, note) in enumerate(NOW):
        y = 84 + i * 52
        cy = y - ty.cap_middle(16, 600)
        items += [f'<circle cx="{x + 4}" cy="{cy:.1f}" r="8" fill="{t.accent_soft}"/>'
                  f'<circle cx="{x + 4}" cy="{cy:.1f}" r="3.5" fill="{t.accent}"/>',
                  ty.fit(ty.text(title, x + 22, y, 16, 600, t.text), room, title),
                  ty.fit(ty.text(note, x + 22, y + 21, 13.5, 400, t.text_2), room, note)]
    return lay(kit.micro("Now", x, 46, t), *items)


def stack_card(w: float, t: Theme) -> Layer:
    x, room, baseline = 28, w - 56, 94
    pieces: list[Layer | ty.Run | str] = []
    cx = x
    for i, word in enumerate(MAIN_STACK):
        if i:
            cy = baseline - ty.cap_middle(26, 600)
            pieces.append(f'<circle cx="{cx + 10:.1f}" cy="{cy:.1f}" r="3" fill="{t.accent}"/>')
            cx += 20
        run = ty.text(word, cx, baseline, 26, 600, t.text, tracking=-0.02)
        pieces.append(run)
        cx += run.width
    if cx - x > room:
        raise ValueError("the main stack does not fit its card")
    chips, _ = kit.chip_row(x, 124, tuple((None, s) for s in MORE_STACK), room, t)
    return lay(kit.micro("Stack", x, 46, t), *pieces, chips)


def about(t: Theme) -> Scene:
    cw, h = (W - GAP) / 2, 240
    left = kit.card_ground("about-clip", cw, h, t, ((30, 270, 210), (400, -30, 170)), (0.0, 1.1))
    right = kit.card_ground("about-clip", cw, h, t, ((390, 260, 200), (20, -40, 160)), (1.0, 1.1))
    body = lay(left, now_card(cw, t), f'<g transform="translate({cw + GAP:g} 0)">', right, stack_card(cw, t), "</g>")
    desc = ("Now: " + "; ".join(f"{a}, {b.lower()}" for a, b in NOW) + ". Stack: mostly "
            + ", ".join(MAIN_STACK) + "; also " + ", ".join(MORE_STACK) + ".")
    return Scene(W, h, "About", desc, "", kit.clip_def("about-clip", cw, h), body)
