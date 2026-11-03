#!/usr/bin/env python3
"""Draws the profile's pictures in Edge's style, each in a dark and a light version.

    pip install -r build/requirements.txt
    python build/build.py                   writes assets/*.svg
    python -m unittest discover -s build    checks them

The README shows the dark or the light file to match the reader's GitHub theme.
The running line of projects reads build/repos.json (see repos.py) and projects.json.
"""
from __future__ import annotations

import os

import kit
import repos
import scenes
import ticker
from tokens import THEMES

SCENES = {
    "hero": scenes.hero,
    "edge": scenes.edge,
    "projects": lambda theme: ticker.ticker(theme, repos.current_projects()),
    "about": scenes.about,
}
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def write_all(out: str = ASSETS) -> list[str]:
    os.makedirs(out, exist_ok=True)
    paths = []
    for name, draw in SCENES.items():
        for theme in THEMES:
            path = os.path.join(out, f"{name}-{theme.name}.svg")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(kit.render(draw(theme), theme))
            paths.append(path)
    return paths


def main() -> None:
    for path in write_all():
        print(f"assets/{os.path.basename(path)}  {os.path.getsize(path):,} bytes")


if __name__ == "__main__":
    main()
