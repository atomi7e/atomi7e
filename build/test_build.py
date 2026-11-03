"""Checks that the profile pictures build, stay well-formed and keep text inside its boxes.

    python -m unittest discover -s build
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build  # noqa: E402
import kit  # noqa: E402
import repos  # noqa: E402
import ticker  # noqa: E402
import typeset  # noqa: E402
from tokens import DARK  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.out = tempfile.mkdtemp()
        cls.files = build.write_all(cls.out)

    def test_every_scene_in_both_themes(self) -> None:
        names = sorted(os.path.basename(p) for p in self.files)
        expected = sorted(f"{scene}-{theme}.svg" for scene in build.SCENES for theme in ("dark", "light"))
        self.assertEqual(names, expected)

    def test_files_are_well_formed_and_outlined(self) -> None:
        for path in self.files:
            root = ET.parse(path).getroot()
            self.assertEqual(root.tag, SVG + "svg", path)
            # an image cannot load fonts, so no live text may be left
            self.assertIsNone(root.find(f".//{SVG}text"), path)
            ids = {el.get("id") for el in root.iter() if el.get("id")}
            for use in root.iter(SVG + "use"):
                self.assertIn(use.get("href", "").lstrip("#"), ids, path)
            with open(path, encoding="utf-8") as fh:
                for ref in re.findall(r"url\(#([\w-]+)\)", fh.read()):
                    self.assertIn(ref, ids, path)

    def test_files_stay_small(self) -> None:
        # the running line grows about 2KB a project; everything else is fixed
        for path in self.files:
            limit = 600_000 if "projects" in os.path.basename(path) else 200_000
            self.assertLess(os.path.getsize(path), limit, path)

    def test_readme_points_at_built_files(self) -> None:
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            refs = set(re.findall(r"assets/([\w-]+\.svg)", fh.read()))
        built = {os.path.basename(p) for p in self.files}
        self.assertTrue(refs)
        self.assertLessEqual(refs, built)


class TypesetTest(unittest.TestCase):
    def test_longer_text_measures_wider(self) -> None:
        self.assertGreater(typeset.measure("Edge app", 15, 400), typeset.measure("Edge", 15, 400))

    def test_heavier_weight_measures_wider(self) -> None:
        self.assertGreater(typeset.measure("Artyom", 40, 600), typeset.measure("Artyom", 40, 400))

    def test_wrap_keeps_lines_within_width(self) -> None:
        text = "Trading journal, calendar, notes, habits and money in one place."
        lines = typeset.wrap(text, 15, 400, 200)
        self.assertGreater(len(lines), 1)
        self.assertEqual(" ".join(lines), text)
        for line in lines:
            self.assertLessEqual(typeset.measure(line, 15, 400), 200)

    def test_fit_refuses_overflow(self) -> None:
        run = typeset.text("Artyom Legezin", 0, 0, 58, 600, "#000")
        with self.assertRaises(ValueError):
            typeset.fit(run, 100, "name")
        self.assertIs(typeset.fit(run, 1000, "name"), run)

    def test_missing_glyph_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            typeset.text("↗", 0, 0, 14, 400, "#000")

    def test_anchor_end_finishes_at_x(self) -> None:
        start = typeset.text("Edge", 0, 0, 20, 600, "#000")
        end = typeset.text("Edge", 100, 0, 20, 600, "#000", anchor="end")
        self.assertAlmostEqual(end.x + end.width, 100, places=2)
        self.assertAlmostEqual(start.x, 0, places=2)


def repo(name: str, **kw: object) -> repos.Repo:
    base = {"description": "About it", "language": "Python", "private": False, "fork": False,
            "size": 10, "pushed_at": "2026-01-01T00:00:00Z"}
    return repos.Repo(name=name, **{**base, **kw})


SETTINGS = repos.Settings(owner="me", skip_empty=True, exclude=frozenset({"hidden"}),
                          overrides={"secret": {"name": "Secret app", "about": "Told on purpose"}})


class ReposTest(unittest.TestCase):
    def test_line_keeps_own_work_newest_first(self) -> None:
        listed = [repo("old", pushed_at="2025-01-01T00:00:00Z"), repo("new", pushed_at="2026-05-01T00:00:00Z"),
                  repo("me"), repo("hidden"), repo("forked", fork=True), repo("empty", size=0),
                  repo("quiet", private=True, topics=(repos.HIDE_TOPIC,))]
        self.assertEqual([p.name for p in repos.projects(listed, SETTINGS)], ["New", "Old"])

    def test_private_description_stays_hidden_unless_given(self) -> None:
        shown = repos.projects([repo("closed", private=True, description="Internal notes"),
                                repo("secret", private=True)], SETTINGS)
        by_name = {p.name: p for p in shown}
        self.assertIsNone(by_name["Closed"].about)
        self.assertEqual(by_name["Secret app"].about, "Told on purpose")
        self.assertTrue(by_name["Secret app"].private)

    def test_public_only_list_keeps_private_ones(self) -> None:
        previous = [repo("closed", private=True), repo("gone")]
        fresh = [repo("open")]
        self.assertEqual({r.name for r in repos.merge(fresh, previous, public_only=True)}, {"open", "closed"})
        self.assertEqual({r.name for r in repos.merge(fresh, previous, public_only=False)}, {"open"})

    def test_snapshot_hides_private_details(self) -> None:
        kept = repos.for_public_eyes([repo("closed", private=True, description="Internal notes"),
                                      repo("hidden", private=True), repo("draft", private=True, size=0),
                                      repo("open", description="Public words")], SETTINGS)
        self.assertEqual({r.name: r.description for r in kept}, {"closed": None, "open": "Public words"})

    def test_committed_snapshot_has_no_private_descriptions(self) -> None:
        for r in repos.load():
            if r.private:
                self.assertIsNone(r.description, r.name)

    def test_snapshot_keeps_only_the_day_and_emptiness(self) -> None:
        kept = repos.for_public_eyes([repo("open", size=5000, pushed_at="2026-03-04T05:06:07Z")], SETTINGS)
        self.assertEqual((kept[0].pushed_at, kept[0].size), ("2026-03-04", 1))

    def test_names_compare_without_case(self) -> None:
        settings = repos.Settings(owner="me", skip_empty=True, exclude=frozenset({"secret-repo"}), overrides={})
        shown = repos.projects([repo("Secret-Repo", private=True), repo("ME")], settings)
        self.assertEqual(shown, [])

    def test_never_pushed_repository_is_read(self) -> None:
        obj = {**{f: getattr(repo("fresh"), f) for f in ("name", "description", "language", "private",
                                                          "fork", "size")}, "pushed_at": None}
        self.assertEqual(repos.parse_repo(obj).pushed_at, "")

    def test_errors_do_not_name_the_repository(self) -> None:
        with self.assertRaises(ValueError) as caught:
            repos.parse_repo({"name": "very-secret-project", "private": "yes"}, "line 7")
        self.assertNotIn("very-secret-project", str(caught.exception))
        self.assertIn("line 7", str(caught.exception))

    def test_humanize(self) -> None:
        self.assertEqual(repos.humanize("my_new-app"), "My new app")

    def test_bad_repository_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            repos.parse_repo({"name": "x", "private": "yes"})

    def test_projects_json_rejects_unknown_keys(self) -> None:
        path = os.path.join(tempfile.mkdtemp(), "projects.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write('{"owner": "me", "pinned": []}')
        with self.assertRaises(ValueError):
            repos.load_settings(path)

    def test_committed_settings_and_snapshot_load(self) -> None:
        self.assertTrue(repos.current_projects())


class TickerTest(unittest.TestCase):
    def build(self, projects: list[repos.Project]) -> ET.Element:
        return ET.fromstring(kit.render(ticker.ticker(DARK, projects), DARK))

    def test_empty_line_still_builds(self) -> None:
        self.assertEqual(self.build([]).tag, SVG + "svg")

    def test_long_texts_are_cut_to_fit(self) -> None:
        long = repos.Project("A very long repository name that goes on and on", "word " * 60, "Python", True)
        self.assertEqual(self.build([long]).tag, SVG + "svg")
        self.assertTrue(typeset.ellipsize(long.name, 15, 600, 180).endswith("…"))
        self.assertLessEqual(typeset.measure(typeset.ellipsize(long.name, 15, 600, 180), 15, 600), 180)

    def test_many_projects_fill_the_line(self) -> None:
        many = [repos.Project(f"Project {i}", None, None, False) for i in range(15)]
        root = self.build(many)
        self.assertGreaterEqual(len([u for u in root.iter(SVG + "use") if u.get("href") == "#set"]), 2)

    def test_loop_has_a_copy_waiting_on_the_left(self) -> None:
        root = self.build([repos.Project("Solo", "One", "Python", False)])
        xs = [float(u.get("x")) for u in root.iter(SVG + "use") if u.get("href") == "#set"]
        self.assertLess(min(xs), 0)

    def test_text_from_github_outside_inter_is_dropped(self) -> None:
        self.assertEqual(typeset.printable("Fast \U0001F680 tool ✨"), "Fast tool")
        self.assertEqual(typeset.printable("Привет"), "")
        odd = repos.Project("Bot \U0001F916", "Привет мир", "Python", False)
        self.assertEqual(self.build([odd]).tag, SVG + "svg")

    def test_one_long_word_is_cut_to_its_line(self) -> None:
        lines = ticker.about_lines("https://example.com/" + "a" * 80, 204)
        self.assertEqual(len(lines), 1)
        self.assertLessEqual(typeset.measure(lines[0], 12.5, 400), 204)


if __name__ == "__main__":
    unittest.main()
