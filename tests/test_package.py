import ast
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILL_DIRS = [
    "./skills/handle-pr-reviews",
    "./skills/md2slack",
    "./skills/ship-prs",
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

    def test_manifest_explicitly_selects_the_three_canonical_skills(self):
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

    def test_all_skills_have_canonical_directories_without_variants(self):
        self.assertFalse((ROOT / "variants").exists())
        directories = sorted(path.parent for path in (ROOT / "skills").rglob("SKILL.md"))
        self.assertEqual(directories, sorted(ROOT / entry for entry in EXPECTED_SKILL_DIRS))

    def test_ship_prs_keeps_the_pi_workflow_and_explicit_invocation(self):
        directory = ROOT / "skills" / "ship-prs"
        self.assertEqual(self.read_frontmatter(directory)["disable-model-invocation"], "true")
        content = (directory / "SKILL.md").read_text()
        self.assertIn("In Pi, discover the required Matt Pocock skills", content)
        self.assertIn("## 2A. Direct: `/implement`", content)
        self.assertIn("## 2B. Spec-first: the full flow", content)

    def test_package_metadata_prevents_npm_publication_and_has_no_runtime_dependencies(self):
        self.assertIs(self.manifest["private"], True)
        self.assertEqual(self.manifest["version"], "0.1.1")
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
        for path in ROOT.glob("skills/*/SKILL.md"):
            self.assertNotIn("~/.pi/agent/", path.read_text(encoding="utf-8"), str(path))


if __name__ == "__main__":
    unittest.main()
