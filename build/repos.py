#!/usr/bin/env python3
"""The repositories in the running line: the list GitHub gives, shaped by projects.json.

    gh api --paginate "/user/repos?affiliation=owner&per_page=100" \\
        --jq '.[] | {name, description, language, private, fork, size, pushed_at, topics}' > raw.jsonl
    python build/repos.py raw.jsonl                 writes build/repos.json, private ones too
    python build/repos.py raw.jsonl --public-only   for a list read without access to private
                                                    ones: keeps those repos.json already has

repos.json is committed, so the pictures build the same offline, in tests and in Actions.
A private repository shows its name and language; its description stays hidden unless
projects.json gives one, since it was written for a private page. projects.json is public,
so a repository whose very name should stay unseen gets the topic hide-from-profile instead.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, replace

HERE = os.path.dirname(os.path.abspath(__file__))
REPOS_JSON = os.path.join(HERE, "repos.json")
PROJECTS_JSON = os.path.join(HERE, "..", "projects.json")
HIDE_TOPIC = "hide-from-profile"


@dataclass(frozen=True)
class Repo:
    name: str
    description: str | None
    language: str | None
    private: bool
    fork: bool
    size: int
    pushed_at: str
    topics: tuple[str, ...] = ()


@dataclass(frozen=True)
class Settings:
    owner: str
    skip_empty: bool
    exclude: frozenset[str]
    overrides: dict[str, dict[str, str]]


@dataclass(frozen=True)
class Project:
    name: str
    about: str | None
    language: str | None
    private: bool


def _need(cond: bool, message: str) -> None:
    if not cond:
        raise ValueError(message)


def parse_repo(obj: object, where: str = "a repository") -> Repo:
    """Errors name the place, never the repository: Actions logs of a public repository are public."""
    _need(isinstance(obj, dict), f"{where} is not an object")
    types = {"name": str, "description": (str, type(None)), "language": (str, type(None)),
             "private": bool, "fork": bool, "size": int, "pushed_at": (str, type(None))}
    for key, kind in types.items():
        _need(isinstance(obj.get(key), kind), f"{where}: {key} has an unexpected value")
    topics = obj.get("topics") or []
    _need(isinstance(topics, list) and all(isinstance(x, str) for x in topics), f"{where}: topics is not a list")
    fields = {key: obj[key] for key in types}
    return Repo(**{**fields, "pushed_at": fields["pushed_at"] or ""}, topics=tuple(topics))


def read_lines(path: str) -> list[Repo]:
    """One JSON object per line, as gh api --jq '.[] | {...}' prints them."""
    with open(path, encoding="utf-8-sig") as fh:      # Windows shells like to add a BOM
        return [parse_repo(json.loads(line), f"line {i}") for i, line in enumerate(fh, 1) if line.strip()]


def load(path: str = REPOS_JSON) -> list[Repo]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [parse_repo(obj, f"repos.json item {i}") for i, obj in enumerate(json.load(fh), 1)]


def save(repos: list[Repo], path: str = REPOS_JSON) -> None:
    ordered = sorted(repos, key=lambda r: r.name.lower())
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump([asdict(r) for r in ordered], fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def merge(fresh: list[Repo], previous: list[Repo], public_only: bool) -> list[Repo]:
    """fresh as is; a public-only fresh list keeps the private repositories seen before."""
    if not public_only:
        return list(fresh)
    known = {r.name.lower() for r in fresh}
    return [*fresh, *(r for r in previous if r.private and r.name.lower() not in known)]


def load_settings(path: str = PROJECTS_JSON) -> Settings:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    _need(isinstance(raw, dict), "projects.json should hold one object")
    unknown = set(raw) - {"owner", "skip_empty", "exclude", "projects"}
    _need(not unknown, f"projects.json: unknown keys {sorted(unknown)}")
    _need(isinstance(raw.get("owner"), str), "projects.json: owner should be your GitHub login")
    exclude = raw.get("exclude", [])
    _need(isinstance(exclude, list) and all(isinstance(x, str) for x in exclude),
          "projects.json: exclude should be a list of repository names")
    overrides = raw.get("projects", {})
    _need(isinstance(overrides, dict), "projects.json: projects should map repository names to texts")
    for repo, texts in overrides.items():
        _need(isinstance(texts, dict) and set(texts) <= {"name", "about"}
              and all(isinstance(v, str) and v.strip() for v in texts.values()),
              f'projects.json: "{repo}" may only have a "name" and an "about", both text')
    # GitHub treats repository names without regard to case, and so does this list
    return Settings(raw["owner"].lower(), bool(raw.get("skip_empty", True)),
                    frozenset(x.lower() for x in exclude), {k.lower(): v for k, v in overrides.items()})


def humanize(repo_name: str) -> str:
    """my_new-app becomes "My new app", until projects.json gives a better name."""
    words = repo_name.replace("_", " ").replace("-", " ").split()
    text = " ".join(words) or repo_name
    return text[0].upper() + text[1:]


def is_shown(r: Repo, settings: Settings) -> bool:
    name = r.name.lower()
    return (not r.fork and name != settings.owner and name not in settings.exclude
            and HIDE_TOPIC not in r.topics and not (settings.skip_empty and r.size == 0))


def for_public_eyes(repos: list[Repo], settings: Settings) -> list[Repo]:
    """What may be committed to this public repository: private ones only when the line
    shows them anyway, and never with their description or topics. Every entry keeps
    just the day of its last push and whether it is empty, which is all the line needs:
    no activity trace to the minute, and no commit for every push somewhere else."""
    kept = [r for r in repos if not r.private or is_shown(r, settings)]
    return [replace(r, pushed_at=r.pushed_at[:10], size=min(r.size, 1),
                    **({"description": None, "topics": ()} if r.private else {}))
            for r in kept]


def projects(repos: list[Repo], settings: Settings) -> list[Project]:
    """What the line shows: own work, newest push first."""
    shown = sorted((r for r in repos if is_shown(r, settings)), key=lambda r: r.name.lower())
    shown.sort(key=lambda r: r.pushed_at, reverse=True)     # stable: same day, by name
    result = []
    for r in shown:
        texts = settings.overrides.get(r.name.lower(), {})
        about = texts.get("about") or (None if r.private else r.description)
        result.append(Project(texts.get("name") or humanize(r.name), about, r.language, r.private))
    return result


def current_projects() -> list[Project]:
    return projects(load(), load_settings())


def main(argv: list[str]) -> None:
    if not argv or argv[0].startswith("-"):
        raise SystemExit(__doc__)
    fresh = read_lines(argv[0])
    repos = for_public_eyes(merge(fresh, load(), public_only="--public-only" in argv), load_settings())
    save(repos)
    print(f"build/repos.json: {len(repos)} repositories, {sum(r.private for r in repos)} private")


if __name__ == "__main__":
    main(sys.argv[1:])
