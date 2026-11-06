---
name: ship-prs
description: Turn a topic into a series of small, independently-shippable PRs — grill it, slice it, then build-and-open each PR one slice at a time.
disable-model-invocation: true
---

# Ship PRs

Take the topic the user gave and ship it as **slices**: the smallest PRs that each merge to `main` on their own. The work runs slice by slice, end to end — never as one big batch.

A **slice** is one PR that is independently shippable: it merges to `main` alone, without waiting for any later slice, and merging it never breaks prod. Every PR must contain no more than **300 changed lines** (insertions plus deletions), counting production code, tests, migrations, and configuration. This is a hard limit, not a target: if a slice would exceed 300 changed lines, split it into additional independently shippable slices before building. Do not exceed the limit because of urgency, dependencies, migrations, tests, or review convenience. Prefer many small slices over one large PR — small is easier to review. Slices may **stack** (branch off the previous slice's branch instead of `main`) when one genuinely depends on another; a stacked slice is still scoped so its own merge is safe.

## 1. Grill the topic

Load and follow the `grilling` skill on the topic the user passed in. Ask grilling questions strictly one at a time: wait for the user's answer before asking the next question, and never batch multiple questions in one message. Resolve every design branch and dependency before moving on.

**Done when:** you and the user share a clear, complete understanding of what's being built.

## 2. Propose the slice plan

Break the work into the smallest set of slices. For each, the merge-safety test must hold: it ships to `main` alone and merging it can't break prod. Decide which slices stack and which are independent.

Present the plan to the user: the number of slices, each slice's scope in one line, and its branch base (`main` or the slice it stacks on). If the whole topic is already small and clear, propose a single slice and say so.

**Done when:** the user has signed off on the number of slices and their scope. Do not build before sign-off.

## 3. Choose the implementation workflow

After the user signs off on the slice plan, and before isolating or building any slice, ask explicitly:

> Do you want to enable `subagent-driven-development` for this run? Reply yes or no.

Wait for an explicit answer. Do not infer the choice from urgency, previous preferences, or approval of the slice plan. Apply the answer to every approved slice unless the user asks to change it.

**Done when:** the user has answered yes or no.

## 4. Ship each slice, one at a time

Loop over the approved slices **in order**. For each slice, run the full cycle before touching the next one:

1. **Isolate.** Load and follow `using-git-worktrees` to create a dedicated worktree so parallel agents never collide. Branch off `main` for an independent slice, off the previous slice's branch for a stacked one.
2. **Build.** If enabled, load and follow `subagent-driven-development`, treating this slice's scope as its plan — fresh implementer subagent per task, TDD, task review, and the final whole-branch review. If disabled, skip `subagent-driven-development` and implement directly in the isolated worktree while preserving the repository's testing and review requirements. (This `create-pr` step replaces SDD's finishing-a-development-branch.)
3. **Open the PR.** Load and follow `create-pr` to open the slice's pull request **as a draft** (`gh pr create --draft`). Leave it for the user to mark ready for review.
4. **Record** the slice's PR title, link, and one-line summary, then move to the next slice.

**Done when:** every approved slice has an open PR.

**Never batch.** Building every slice and only then opening the PRs is the exact failure this skill exists to prevent. A slice is not finished until its PR is open; the next slice's build does not start before that.

## 5. Report

For every PR opened, output one block:

- **Title** — the PR title
- **Link** — the PR URL
- **What it does** — one line
