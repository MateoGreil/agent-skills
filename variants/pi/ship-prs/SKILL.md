---
name: ship-prs
description: Build a topic through a confirmed direct or spec-first workflow, publish draft PRs of at most 300 changed lines, and offer a retrospective.
disable-model-invocation: true
---

# Ship PRs

Choose the workflow for the **whole topic** with the user, then build and publish it as small draft PRs. The workflow choice and PR boundaries are separate decisions: a large feature can need a spec and still ship through several small PRs.

**PR budget:** every PR is limited to **300 changed lines**, additions plus deletions across all changed text files, including tests, migrations, configuration and documentation. This is a hard ceiling, not a target. Each slice must be safe to merge onto its declared base; dependencies may use stacked PRs.

## Execute the skills

In Pi, discover the required Matt Pocock skills by name in the available skill list or configured skill locations. Read each skill's full `SKILL.md` at its discovered location and follow its instructions. Use absolute paths for tool calls and resolve bundled references relative to that skill's directory. When a loaded skill asks for a Skill tool that this harness lacks, discover the referenced skill by name, then read and follow its full instructions instead.

This explicit invocation of `ship-prs` authorizes the selected chain; keep each skill's user-confirmation gates. If a required skill is unavailable, report the blocker rather than substituting an improvised workflow. Repository instructions govern isolation, branching, artifacts and publication; surface any conflict before taking the affected action.

## 1. Recommend a route and ask

Inspect the request, relevant repository instructions and enough existing code to assess scope, uncertainty, dependencies and risk. Use facts you can inspect; leave product and design decisions to the user.

Recommend one route:

- **Direct → `/implement`** for a localized, well-understood change whose implementation and review fit in one context window, with little unresolved design or rollout risk.
- **Spec-first → `/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement-spec`** for several dependent deliverables, a multi-session build, substantial unresolved design, or consequential architecture, contract, data or rollout choices.

Give one or two concrete reasons and ask, in the user's language:

> Je recommande **[direct / avec spec]**, parce que **[raisons propres à ce sujet]**. Tu valides ce parcours, ou tu préfères l'autre ?

Wait for the user's choice before planning artifacts, implementation or worker dispatch. Approval of the topic is not approval of a route.

**Done when:** the user has explicitly selected direct or spec-first.

If a selected phase requires an issue tracker and it is not configured, load `setup-matt-pocock-skills` and complete its confirmation gates before that phase.

## 2A. Direct: `/implement`

Create or reuse the task workspace and branch according to repository policy. Load and follow `implement`, using the user's request or issue and confirmed behavior as its input. A formal spec is not required for this route; `implement` owns its TDD, verification, code review and commit cycle.

Keep the work within the agreed scope and plan for the PR budget. If investigation reveals substantial unresolved decisions or a multi-session effort, pause and recommend switching to spec-first; wait for the user's agreement before switching.

**Done when:** the agreed behavior is implemented, verified, reviewed and committed. Continue to section 3.

## 2B. Spec-first: the full flow

Keep grilling, spec synthesis and ticket decomposition in the same conversation so the decisions remain primary context. Load each phase when it is reached, and complete it before starting the next.

1. **`grill-with-docs`** — follow its `grilling` and `domain-modeling` instructions, including rounds of currently answerable questions. Resolve the design branches and record the agreed vocabulary and qualifying ADRs.
   **Done when:** the design frontier is empty and the user confirms the shared understanding.
2. **`to-spec`** — synthesize the settled discussion rather than starting a new interview. Check that every agreed behavior, constraint and relevant edge case is represented, with testing decisions and explicit scope boundaries. Return unresolved decisions to grilling before finalizing the spec.
   **Done when:** testing seams are confirmed and the complete spec is published to the configured tracker.
3. **`to-tickets`** — turn the spec into vertical, verifiable tickets with blocking edges. Account for every spec requirement in acceptance criteria. Propose PR-sized slices and their bases as part of the breakdown, estimating against the PR budget rather than treating the whole spec as one PR.
   **Done when:** the user approves the granularity and dependencies, and the tickets are published with their blocking relationships.
4. **`implement-spec`** — build the task graph on one integration branch using the skill's implementers, integration process and final code review. Keep ticket work attributable so it can be prepared as the approved PR slices.
   **Done when:** every ticket's acceptance criteria are satisfied and the integrated implementation passes verification and code review.

**Publication boundary:** `ship-prs` owns PR creation, draft status, tracker closure and review follow-up. Use `implement-spec` for implementation, verification and ticket integration; defer its automatic draft creation and ready-for-review/closure actions to section 3. The integration branch may exceed the PR budget, but must not itself become an oversized PR. Keep it available until the small PR branches are prepared, then clean up temporary worktrees according to repository policy.

## 3. Publish within the PR budget

For either route:

1. Prepare the verified work as independently merge-safe PR slices. Use the repository's target branch for independent slices and the declared predecessor branch for stacked slices. Reuse the approved ticket breakdown on the spec-first route; a small direct change normally needs one PR.
2. Fetch the current remote base and measure **each actual PR diff** using `git diff --numstat <PR-base>...<PR-head>`, summing additions plus deletions. A stacked PR is measured against its own declared base, not against the entire integration branch. Check this before creation and before every subsequent push.
3. If a slice exceeds the budget, split it into smaller merge-safe slices and confirm the revised boundaries with the user before publishing. Verify the intermediate branches, not only the final integrated state. If a safe split is blocked, explain why and wait for a compatible plan; the budget is not waived.
4. Load `pr` when writing each PR body. Push the verified slice and create its PR **as a draft**, using `gh` for GitHub or `tea` for Forgejo. Reuse an existing PR when appropriate and preserve any readiness change the user made. Open each ready slice without waiting for other PRs to be approved. Leave readiness and merging to the user.
5. Link the spec and relevant tickets. Add closing references only to PRs that fully complete the referenced work; partial contributions use ordinary references. Follow the configured tracker's closure rules without claiming that opening a draft means the work has merged.
6. Share each PR's title, URL, scope, measured line count and verification results. Report its actual review status on the latest head.

**Done when:** every approved slice has a verified PR within budget, with new PRs in draft and existing user-selected readiness preserved, or a specific publication blocker has been reported.

## 4. Follow reviews and report

For incoming review findings, discover `handle-pr-reviews` by name, read its full `SKILL.md` at the discovered location, and follow it with the PR URL. Preserve the agreed design and the PR budget through every fix and push.

Keep stacked branches aligned with changes to their bases, propagating updates from bottom to top. Before pushing a changed base or retargeting a PR, verify and measure every affected PR's prospective comparison, including dependents whose heads are unchanged; block any transition that would breach the PR budget. Confirm the actual remote comparisons afterward. Re-verify after rebasing and use `--force-with-lease` when an authorized stack update needs a force-push. After a base merges, move its dependent PR onto the target branch without replaying already-merged changes.

Where the harness supports background review watchers with wake-up notifications, keep one watcher per PR until approval on its latest head. Otherwise report pending review without claiming an active watch. Pending review does not block the publication report or the retrospective offer.

Report each PR's title, link, scope, line count, checks and latest-head review status, along with outstanding findings or blockers.

## 5. Offer `/retro`

After the implementation and publication report, ask the user whether they want a retrospective on this run. Ask on both routes, while the session context is still available:

> Souhaites-tu lancer `/retro` sur ce run ?

Wait for the answer. On yes, load and follow `retro` using this session as the primary source. On no, finish without running it.
