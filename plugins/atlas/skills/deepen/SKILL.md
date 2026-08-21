---
name: deepen
description: Use when a design bundle exists under design/ and it needs deepening — an open waypoint to resolve with the operator, landed research to sweep onto the maps, or a quiet subtree whose resolved design is ready to cut into backlog issues.
---

# Wayfinding: Deepen

Deepen the bundle: resolve the focus waypoint with the operator, keep the maps honest, and when the bookkeeping sweep leaves a subtree quiet, propose cutting its design into backlog issues.

**REQUIRED BACKGROUND:** Read `${CLAUDE_PLUGIN_ROOT}/references/wayfinding.md` before anything else. The conversation discipline, the mutability rule, the frontmatter trust contract, and the resolution bookkeeping there are the substance of this skill; this file is the flow around them.

## Flow

1. **Cut a working branch from main** — or continue the previous session's branch if it hasn't merged yet, rather than stacking a second. Load the maps on the path from the root to the focus region — the low-resolution view. Zoom into individual waypoints on demand during conversation; don't front-load them.

2. **Sweep landed agent work.** Any research waypoint whose `## Findings` arrived since the last session — including findings sitting uncommitted on the branch from agents that outlived their session: gist it onto its map (Decisions so far) and run the reference's resolution bookkeeping before new work starts. A Prototype waypoint whose `## Artifact` has landed is different: it is *ripe, not resolved* — commit it, leave it on the Frontier, and surface it when recommending a focus; the operator reacting to the artifact is what resolves it. Any open `## Challenge` the auditor left — on any concept — is surfaced to the operator this session: they re-affirm the challenged text (delete the section) or amend it per the reference's mutability rule. A challenge is never closed without them.

3. **Fix the focus.** The operator usually arrives with a waypoint picked. If they don't name one, recommend the frontier waypoint you judge most load-bearing — the one whose answer unblocks or reshapes the most — and say why. The session centers on its Question.

4. **Resolve it** by the reference's conversation discipline: mine the ramble, reflect back `decided X because Y`, challenge contradictions against the map, pose one question with a recommendation. Record only what the discipline licenses — stated decisions with their why, interpretations and spillover on confirmation, gaps never. **No why, no record:** a decision whose reason wasn't stated or confirmed stays in the conversation until it is — and the recorded Decision carries the operator's `verified` stamp, which asserts that confirmation happened. The reference's mutability section owns both rules.

5. **Bookkeep** per the reference: Decision and stamp into the waypoint (for a Prototype, that's also when the artifact and its `## Artifact` section are deleted), gist onto its map, sweep fog/blocked/stale prose, cut newly-sharp waypoints, dispatch `atlas:waypoint-researcher` for new research and `atlas:waypoint-prototyper` for new prototypes (brief beneath the Question first; both plain unnamed background dispatches — never pass `name`) — and **check for quiet**, walking up from the resolved waypoint's map.

6. **Lint and commit — the session continues until the operator ends it.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint_bundle.py" design/` and fix every finding before committing. A resolved focus is the middle of a deepen, not its end: recommend the next most load-bearing frontier waypoint and return to step 3, or follow the operator wherever they go next. Never propose landing because bookkeeping finished — session close is the operator's signal, not yours to infer.

7. **At the operator's session close: dispatch the auditor, then land.** Dispatch `atlas:wayfinding-auditor` — a plain **unnamed** background dispatch; a named (teammate) dispatch silently loses its report — with the bundle root and every concept this session wrote or amended; its challenges land in the working tree whenever they land, swept by the next session. Then ask the operator to land the session on main — **their typed yes is the approval**; fast-forward merge, push, delete the branch, per the reference's version-control contract. If they defer, push the branch and stop; a PR exists only if they ask for one.

## The pull to build

Somewhere along the way a resolved waypoint will look like ten minutes of code, and the operator may say "just set it up while we're here." **The pull to do the work is the signal you've reached the map's edge, not permission to cross it.** The doctrine's project-wide invariant — no code ships from the bundle — is the standing rule; building from a design branch buries a feature where no verifier, spec, or reviewer will ever meet it.

Record the decision, then say where the build actually lands: a slice in the subtree's eventual issues, or — if the operator genuinely wants it today — its own change through the normal pipeline, started outside the bundle. That costs one sentence now and keeps the bundle a design record instead of a half-shipped branch.

## Quiet subtrees — proposing the cut

The bundle never runs out; subtrees do. When the bookkeeping sweep leaves a subtree quiet — empty Frontier, empty Blocked, no fog, in its map and every map beneath it — **proposing the commitment conversation is part of the sweep, not a judgment call.** Name the highest quiet node and propose cutting its issues now. The operator decides: hold the conversation, or park it and keep deepening elsewhere — a parked proposal is re-raised next time the subtree is touched, never queued in a file.

The conversation itself follows the reference's quiet-subtrees section: slice the subtree's design into issues (a quiet subtree cuts alone — it never waits for siblings), and the operator rules which slices are committed work and which are drafts. Filing them, and writing `## Issues cut` back into the map, is the backlog tool's job, not the bundle's — the map owns that section's format and is the one home of cross-issue ordering.

Two failure modes, both fatal to the doctrine:

| Pull | Reality |
|---|---|
| "The whole bundle isn't done, so it's too early to cut issues" | The whole bundle is never done. Quiet is evaluated per subtree; waiting for the tree is waiting forever, and the bundle becomes the place design goes to continue forever. |
| "It went quiet, so the slicing is settled" | Quiet triggers the *proposal*, nothing else. Which slices are committed work is the operator's call, made in the conversation — assuming it from quietness assumes the operator's yes. |
