import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const sdkEntry = new URL(import.meta.resolve("@earendil-works/pi-coding-agent"));
const { DefaultPackageManager } = await import(new URL("./core/package-manager.js", sdkEntry));
const { SettingsManager } = await import(new URL("./core/settings-manager.js", sdkEntry));
const { loadSkills } = await import(new URL("./core/skills.js", sdkEntry));
const { parseFrontmatter } = await import(new URL("./utils/frontmatter.js", sdkEntry));
const manifest = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
const expectedNames = ["handle-pr-reviews", "md2slack", "ship-prs"];
const agentDir = join(root, "tests", "unused-agent-dir");

function discover(skillPaths) {
  return loadSkills({ cwd: root, agentDir, skillPaths, includeDefaults: false });
}

test("Pi parses valid portable frontmatter in both selectable sets", () => {
  const directories = [...manifest.pi.skills, "./variants/vibe/ship-prs"];
  for (const entry of directories) {
    const file = join(root, entry, "SKILL.md");
    const { frontmatter, body } = parseFrontmatter(readFileSync(file, "utf8"));
    assert.equal(frontmatter.name, basename(dirname(file)));
    assert.match(frontmatter.name, /^[a-z0-9]+(?:-[a-z0-9]+)*$/);
    assert.ok(frontmatter.name.length <= 64);
    assert.equal(typeof frontmatter.description, "string");
    assert.ok(frontmatter.description.trim().length > 0);
    assert.ok(frontmatter.description.length <= 1024);
    assert.ok(body.length > 0);
    if (frontmatter.name === "ship-prs") {
      assert.equal(frontmatter["disable-model-invocation"], true);
    }
  }
});

test("Pi resolves the local manifest to exactly three collision-free skills", async () => {
  const manager = new DefaultPackageManager({
    cwd: root,
    agentDir,
    settingsManager: SettingsManager.inMemory(),
  });
  const resources = await manager.resolveExtensionSources([root], { temporary: true });
  assert.deepEqual(resources.installFailures, []);
  for (const resourceType of ["extensions", "prompts", "themes"]) {
    assert.deepEqual(resources[resourceType], []);
  }
  assert.equal(resources.skills.length, 3);
  assert.ok(resources.skills.every((resource) => resource.enabled));
  const result = discover(resources.skills.map((resource) => resource.path));
  assert.deepEqual(result.diagnostics, []);
  assert.deepEqual(result.skills.map((skill) => skill.name).sort(), expectedNames);
  assert.equal(new Set(result.skills.map((skill) => skill.name)).size, 3);
  const ship = result.skills.find((skill) => skill.name === "ship-prs");
  assert.equal(ship.filePath, join(root, "variants", "pi", "ship-prs", "SKILL.md"));
  assert.equal(ship.disableModelInvocation, true);
  assert.ok(result.skills.filter((skill) => skill.name !== "ship-prs").every((skill) => !skill.disableModelInvocation));
});

test("common skills plus the Vibe variant also discover without a collision", () => {
  const result = discover([
    resolve(root, "skills", "handle-pr-reviews"),
    resolve(root, "skills", "md2slack"),
    resolve(root, "variants", "vibe", "ship-prs"),
  ]);
  assert.deepEqual(result.diagnostics, []);
  assert.deepEqual(result.skills.map((skill) => skill.name).sort(), expectedNames);
  assert.equal(new Set(result.skills.map((skill) => skill.name)).size, 3);
  const ship = result.skills.find((skill) => skill.name === "ship-prs");
  assert.equal(ship.filePath, join(root, "variants", "vibe", "ship-prs", "SKILL.md"));
});
