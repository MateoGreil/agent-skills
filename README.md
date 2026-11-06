# Agent skills

Shared skills for Pi, Vibe and Claude Code, extracted from MateoGreil's dotfiles. Common skills are `handle-pr-reviews` and `md2slack`; `ship-prs` has two intentionally different workflows:

- **Pi:** confirm direct or spec-first, publish draft PRs within a 300-line budget, follow reviews, offer a retrospective.
- **Vibe:** grill, approve slices and the subagent-development choice, then build and open each small draft PR before starting the next.

## Pi

Once the repository and `v0.1.0` tag are published:

```sh
pi install git:github.com/MateoGreil/agent-skills@v0.1.0
```

The explicit `pi.skills` manifest loads exactly three skills: the two common directories and **only** `variants/pi/ship-prs`. It does not recursively load `variants/`, avoiding the two `ship-prs` names colliding. Remove equivalent old local skill copies before enabling the package; restart Pi or use `/reload` afterward.

## Vibe and Claude Code

Clone the repository and link individual common skill directories plus **one** chosen `ship-prs` variant into your agent's skill directory. For example, for Vibe:

```sh
repo="$HOME/Projects/agent-skills"
skills="$HOME/.vibe/skills"
mkdir -p "$skills"
ln -s "$repo/skills/handle-pr-reviews" "$skills/handle-pr-reviews"
ln -s "$repo/skills/md2slack" "$skills/md2slack"
ln -s "$repo/variants/vibe/ship-prs" "$skills/ship-prs"
```

For Claude Code use `~/.claude/skills` as the destination, selecting the variant whose workflow and prerequisites you intend to use. Move conflicting existing skill directories aside yourself; the example does not overwrite them. Link neither the repository root nor the whole `variants/` tree into a recursively scanned skill location.

The Matt Pocock skills referenced by the Pi workflow and the skills referenced by the Vibe workflow are **not bundled**. Install the chosen workflow's prerequisites separately. Skill references are resolved by name and advertised/configured location; read their full instructions and preserve their approval gates. Missing skills or required harness capabilities are blockers, not permission to improvise another workflow. PR operations require authenticated `gh` or `tea` as appropriate.

## md2slack requirements

- Python **>=3.10**; the converter and API sender use only the standard library. There are no npm runtime dependencies.
- The initial clipboard implementation is **Linux-only**, requiring PyGObject, GTK4 and an X11/Wayland session (`python3-gi`, `gir1.2-gtk-4.0` on Ubuntu). Clipboard verification uses `xclip` where available. No macOS clipboard implementation is included.
- Direct Slack posting requires locally authenticated [slackcli](https://github.com/ksred/slackcli) browser-session credentials. Its configuration stays on the user's machine and is not shipped. Tests use dummy credentials and never post to Slack or touch the clipboard.

Scripts are beside [`skills/md2slack/SKILL.md`](skills/md2slack/SKILL.md); resolve their paths relative to that skill directory. See its [README](skills/md2slack/README.md) for the two delivery paths.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

These offline tests cover conversion, API payloads, fallback/error behavior and the manifest/frontmatter contract. For integration validation with an already available **Pi 1.5.0 SDK**, make its installed `node_modules` resolvable here (an ignored temporary symlink is sufficient), then run:

```sh
node --test tests/package.test.mjs
```

This resolves the local package without installing it or changing agent settings, validates frontmatter with Pi's parser and confirms three collision-free skills with the Pi variant selected.

## Attribution and licensing

Credit for the macOS clipboard idea behind `md2slack` belongs to [loslcrd/md2slack](https://github.com/loslcrd/md2slack). Its pandoc/AppleScript implementation and documentation are not bundled. The two md2slack documents here are original writing based on the interfaces of this package's Linux/API scripts.

The retrieved upstream inline Python was compared with all three bundled scripts. No substantial copied code block was identified; the shared fragments were limited to ordinary Markdown cell-parsing and short Python idioms. This comparison concerns the retrieved upstream content, not a legal determination of every dependency's provenance.

Upstream has no declared license. No license has been selected for this package: `license: UNLICENSED` does not grant redistribution rights or substitute for upstream terms. `private: true` prevents accidental npm publication, not GitHub publication. No MIT license has been assigned.
