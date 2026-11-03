"""The running line: every repository as a small tile, sliding by under a calm card.

The set of tiles is drawn once and repeated with <use> until it covers the card,
then the row slides left by exactly one set, so the loop has no seam. The ends
fade into the card, as content does under Edge's floating bars.
"""
from __future__ import annotations

import math

import kit
import shapes as sh
import typeset as ty
from kit import PAD, R_TILE, W, Layer, Scene, lay
from repos import Project
from tokens import Theme

ITEM_W, ITEM_H, ITEM_GAP = 236, 112, 12
TRACK_Y = 80
SPEED = 34                       # px a second: calm enough to read a tile as it passes
REPOS_URL_LABEL = "All repositories"

# GitHub's own language colours, so a dot reads the same as on a repository page
LANGUAGE_COLOURS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "HTML": "#e34c26",
    "CSS": "#663399", "Swift": "#F05138", "Jupyter Notebook": "#DA5B0B", "Shell": "#89e051",
    "Go": "#00ADD8", "Rust": "#dea584", "Java": "#b07219", "Kotlin": "#A97BFF", "C#": "#178600",
    "C++": "#f34b7d", "C": "#555555", "Dart": "#00B4AB", "Vue": "#41b883", "PHP": "#4F5D95",
}


def about_lines(about: str, room: float) -> list[str]:
    """Up to two lines; a line ends in an ellipsis when the text runs on or a word is too long."""
    lines = ty.wrap(about, 12.5, 400, room)
    if len(lines) > 2:
        lines = [lines[0], " ".join(lines[1:])]
    return [ty.ellipsize(line, 12.5, 400, room) for line in lines]


def item(x: float, p: Project, t: Theme) -> Layer:
    room = ITEM_W - 32
    name_room = room - (22 if p.private else 0)
    label = ty.printable(p.name, 600) or "Untitled"     # names and texts may come from GitHub
    about = ty.printable(p.about) if p.about else ""
    name = ty.fit(ty.text(ty.ellipsize(label, 15, 600, name_room), x + 16, 30, 15, 600, t.text), name_room, label)
    parts: list[Layer | ty.Run | str] = [sh.tile(sh.rect_shape(x, 0, ITEM_W, ITEM_H, R_TILE), t), name]
    if p.private:
        parts.append(sh.icon("lock", x + ITEM_W - 16 - 14, 18, 14, t.text_3))
    if about:
        parts += [ty.text(line, x + 16, 52 + i * 17, 12.5, 400, t.text_2)
                  for i, line in enumerate(about_lines(about, room))]
    else:
        parts.append(ty.text("Private code" if p.private else "No description yet", x + 16, 52, 12.5, 400, t.text_3))
    language = ty.printable(p.language) if p.language else ""
    if language:
        colour = LANGUAGE_COLOURS.get(language, t.text_3)
        parts += [f'<circle cx="{x + 20:g}" cy="{ITEM_H - 16 - 4:g}" r="4" fill="{colour}"/>',
                  ty.text(ty.ellipsize(language, 12, 400, room - 14), x + 30, ITEM_H - 16, 12, 400, t.text_3)]
    return lay(*parts)


def header(n: int, t: Theme) -> Layer:
    title = ty.text("Projects", PAD, 54, 22, 600, t.text, tracking=-0.01)
    count, _ = kit.chip(PAD + title.width + 12, 54 - ty.cap_middle(22, 600) - 15, str(n), t)
    return lay(title, count, open_pill(W - PAD, 54 - ty.cap_middle(22, 600) - 16, t))


def open_pill(right: float, y: float, t: Theme) -> Layer:
    """Glass button naming where the picture links to: the repositories tab."""
    h, pad, size = 32, 14, 14
    label_w = ty.measure(REPOS_URL_LABEL, 13, 500)
    x = right - (pad + label_w + 6 + size + 12)
    return lay(sh.glass(sh.rect_shape(x, y, right - x, h, h / 2), t),
               ty.text(REPOS_URL_LABEL, x + pad, y + h / 2 + ty.cap_middle(13, 500), 13, 500, t.accent_ink),
               sh.icon("arrow-up-right", x + pad + label_w + 6, y + (h - size) / 2, size, t.accent_ink))


def track(projects: list[Project], t: Theme) -> tuple[Layer, str, str]:
    """The sliding row, the defs it repeats and its CSS."""
    if not projects:
        note = ty.text("Repositories appear here once they are pushed", W / 2, TRACK_Y + ITEM_H / 2, 14, 400,
                       t.text_3, anchor="middle")
        return lay(note), "", ""
    tiles = lay(*(item(i * (ITEM_W + ITEM_GAP), p, t) for i, p in enumerate(projects)))
    span = len(projects) * (ITEM_W + ITEM_GAP)
    copies = math.ceil(W / span) + 1
    # one copy also waits on the left, so the strip there looks the same at the start and the end
    uses = "".join(f'<use href="#set" x="{c * span:g}"/>' for c in range(-1, copies))
    row = (f'<g mask="url(#fade)"><g transform="translate({PAD:g} {TRACK_Y:g})">'
           f'<g class="track">{uses}</g></g></g>')
    defs = (f'<g id="set">{tiles.svg}</g>'
            '<linearGradient id="fade-g" x1="0" y1="0" x2="1" y2="0">'
            f'{sh.stop(0, "#fff", 0)}{sh.stop(.05, "#fff")}{sh.stop(.95, "#fff")}{sh.stop(1, "#fff", 0)}'
            '</linearGradient>'
            f'<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="{TRACK_Y - 20}" width="{W}" height="{ITEM_H + 40}">'
            f'<rect x="0" y="{TRACK_Y - 20}" width="{W}" height="{ITEM_H + 40}" fill="url(#fade-g)"/></mask>')
    css = (f".track{{animation:slide {span / SPEED:.1f}s linear infinite}}"
           f"@keyframes slide{{to{{transform:translateX(-{span:g}px)}}}}")
    return Layer(row, tiles.glyphs), defs, css


def ticker(t: Theme, projects: list[Project]) -> Scene:
    w, h = W, TRACK_Y + ITEM_H + 28
    row, defs, css = track(projects, t)
    ground = kit.card_ground("projects-clip", w, h, t, ((760, 260, 230), (60, -40, 190)), (.02, -.2))
    body = lay(ground, header(len(projects), t), row)
    names = ", ".join(p.name + (" (private)" if p.private else "") for p in projects)
    desc = f"{len(projects)} projects: {names}." if projects else "No projects yet."
    return Scene(w, h, "Projects", desc, css, kit.clip_def("projects-clip", w, h) + defs, body)
