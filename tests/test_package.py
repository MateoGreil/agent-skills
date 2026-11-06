import ast
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILL_DIRS = [
    "./skills/handle-pr-reviews",
    "./skills/md2slack",
    "./variants/pi/ship-prs",
]
EXPECTED_NAMES = ["handle-pr-reviews", "md2slack", "ship-prs"]


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    def read_frontmatter(self, directory):
        path = directory / "SKILL.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "---", str(path))
        closing = lines.index("---", 1)
        fields = {}
        for line in lines[1:closing]:
            key, separator, value = line.partition(":")
            self.assertEqual(separator, ":", str(path))
            self.assertNotIn(key, fields, str(path))
            fields[key] = value.strip()
        self.assertTrue(any(line.strip() for line in lines[closing + 1:]), str(path))
        return fields

    def assert_valid_skill(self, directory):
        fields = self.read_frontmatter(directory)
        self.assertEqual(fields["name"], directory.name)
        self.assertTrue(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]))
        self.assertLessEqual(len(fields["name"]), 64)
        self.assertTrue(fields["description"].strip())
        self.assertLessEqual(len(fields["description"]), 1024)
        return fields

    def test_manifest_explicitly_selects_common_skills_and_only_pi_variant(self):
        resources = self.manifest["pi"]
        self.assertEqual(set(resources), {"extensions", "skills", "prompts", "themes"})
        self.assertEqual(resources["skills"], EXPECTED_SKILL_DIRS)
        for resource in ("extensions", "prompts", "themes"):
            self.assertEqual(resources[resource], [])

    def test_manifest_discovers_three_skill_roots_with_valid_unique_frontmatter(self):
        names = []
        for entry in self.manifest["pi"]["skills"]:
            directory = ROOT / entry
            self.assertEqual(list(directory.rglob("SKILL.md")), [directory / "SKILL.md"])
            names.append(self.assert_valid_skill(directory)["name"])
        self.assertEqual(names, EXPECTED_NAMES)
        self.assertEqual(len(names), len(set(names)))

    def test_common_skills_with_only_vibe_variant_are_also_collision_free(self):
        directories = [ROOT / entry for entry in EXPECTED_SKILL_DIRS[:2]]
        directories.append(ROOT / "variants" / "vibe" / "ship-prs")
        names = [self.assert_valid_skill(directory)["name"] for directory in directories]
        self.assertEqual(names, EXPECTED_NAMES)
        self.assertEqual(len(names), len(set(names)))

    def test_ship_prs_variants_remain_distinct_and_explicitly_invoked(self):
        pi = ROOT / "variants" / "pi" / "ship-prs"
        vibe = ROOT / "variants" / "vibe" / "ship-prs"
        for directory in (pi, vibe):
            self.assertEqual(self.read_frontmatter(directory)["disable-model-invocation"], "true")
        self.assertNotEqual(self.read_frontmatter(pi)["description"], self.read_frontmatter(vibe)["description"])
        self.assertNotEqual((pi / "SKILL.md").read_text(), (vibe / "SKILL.md").read_text())

    def test_package_metadata_prevents_npm_publication_and_has_no_runtime_dependencies(self):
        self.assertIs(self.manifest["private"], True)
        self.assertEqual(self.manifest["version"], "0.1.0")
        self.assertEqual(self.manifest["type"], "module")
        self.assertEqual(self.manifest["license"], "UNLICENSED")
        self.assertIn("pi-package", self.manifest["keywords"])
        self.assertFalse(self.manifest.get("dependencies"))
        self.assertFalse(self.manifest.get("optionalDependencies"))

    def test_scripts_are_beside_the_skill_and_have_valid_python_syntax(self):
        directory = ROOT / "skills" / "md2slack"
        for name in ("md2slack.py", "clip_table.py", "send_slack_table.py"):
            path = directory / name
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        self.assertTrue((directory / "README.md").is_file())

    def test_skill_references_do_not_use_the_original_pi_installation(self):
        for path in [*ROOT.glob("skills/*/SKILL.md"), *ROOT.glob("variants/*/*/SKILL.md")]:
            self.assertNotIn("~/.pi/agent/", path.read_text(encoding="utf-8"), str(path))


if __name__ == "__main__":
    unittest.main()
