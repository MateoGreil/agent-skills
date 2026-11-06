# Changelog

## [0.1.1]

- Move the unchanged Pi `ship-prs` workflow to `skills/ship-prs`.
- Remove the Vibe-specific workflow and the `variants/` layout.
- Update the manifest, documentation and discovery tests for the canonical skill directories.

## [0.1.0]

- Extract the shared `handle-pr-reviews` and Linux `md2slack` skills.
- Preserve the distinct Pi and Vibe `ship-prs` workflows; expose only the Pi variant through the Pi manifest.
- Resolve bundled scripts relative to their skill directory and external skills by discovered name/location.
- Use neutral default intro text for Slack API messages.
- Add offline Python regression tests and Pi SDK discovery/frontmatter verification.
- Credit the upstream macOS idea without bundling its implementation or docs; write original md2slack documentation and leave the package without a selected license.
