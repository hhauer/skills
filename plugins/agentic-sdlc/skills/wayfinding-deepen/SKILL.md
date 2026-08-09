---
name: wayfinding-deepen
description: Use when a design bundle exists under design/ and it needs deepening — an open waypoint to resolve with the operator, landed research to sweep onto the maps, or a quiet subtree whose resolved design is ready to cut into backlog issues.
---

# Wayfinding: Deepen

Deepen the bundle: resolve the focus waypoint with the operator, keep the maps honest, and when the bookkeeping sweep leaves a subtree quiet, propose cutting its design into backlog issues.

**REQUIRED BACKGROUND:** Read `${CLAUDE_PLUGIN_ROOT}/references/wayfinding.md` before anything else. The conversation discipline, the mutability rule, the frontmatter trust contract, and the resolution bookkeeping there are the substance of this skill; this file is the flow around them.

## Flow

1. **Cut a working branch from main** — or continue the previous session's branch if its PR is still open, rather than stacking a second. Load the maps on the path from the root to the focus region — the low-resolution view. Zoom into individual waypoints on demand during conversation; don't front-load them.

2. **Sweep landed research.** Any research waypoint whose `## Findings` arrived since the last session — including findings sitting uncommitted on the branch from agents that outlived their session: gist it onto its map (Decisions so far) and run the reference's resolution bookkeeping before new work starts.

3. **Fix the focus.** The operator usually arrives with a waypoint picked. If they don't name one, recommend the frontier waypoint you judge most load-bearing — the one whose answer unblocks or reshapes the most — and say why. The session centers on its Question.

4. **Resolve it** by the reference's conversation discipline: mine the ramble, reflect back `decided X because Y`, challenge contradictions against the map, pose one question with a recommendation. Record only what the discipline licenses — stated decisions with their why, interpretations and spillover on confirmation, gaps never. **No why, no record:** a decision whose reason wasn't stated or confirmed stays in the conversation until it is — and the recorded Decision carries the operator's `verified` stamp, which asserts that confirmation happened. The reference's mutability section owns both rules.

5. **Bookkeep** per the reference: Decision and stamp into the waypoint, gist onto its map, sweep fog/blocked/stale prose, cut newly-sharp waypoints, dispatch `agentic-sdlc:waypoint-researcher` for new research — and **check for quiet**, walking up from the resolved waypoint's map.

6. **Lint, commit, push, and make sure the session's PR exists.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint_bundle.py" design/` and fix every finding before committing. **Merging is the operator's act, in the Forgejo UI**; no session touches main.

## The pull to build

Somewhere along the way a resolved waypoint will look like ten minutes of code, and the operator may say "just set it up while we're here." **The pull to do the work is the signal you've reached the map's edge, not permission to cross it.** The root map's own destination line — no code ships from the bundle — is the standing rule; building from a design branch buries a feature where no verifier, spec, or reviewer will ever meet it.

Record the decision, then say where the build actually lands: a slice in the subtree's eventual issues, or — if the operator genuinely wants it today — its own change through the normal pipeline, started outside the bundle. That costs one sentence now and keeps the bundle a design record instead of a half-shipped branch.

## Quiet subtrees — proposing the cut

The bundle never runs out; subtrees do. When the bookkeeping sweep leaves a subtree quiet — empty Frontier, empty Blocked, no fog, in its map and every map beneath it — **proposing the commitment conversation is part of the sweep, not a judgment call.** Name the highest quiet node and propose cutting its issues now. The operator decides: hold the conversation, or park it and keep deepening elsewhere — a parked proposal is re-raised next time the subtree is touched, never queued in a file.

The conversation itself follows the reference's quiet-subtrees section: slice the subtree's design into issues (a quiet subtree cuts alone — it never waits for siblings), the operator rules which are approved and which are drafts, cut them with `dev-tools:fj` linking each to the subtree's map, and write `## Issues cut` into that map — an ordered list, build order, the one home of cross-issue ordering.

Two failure modes, both fatal to the doctrine:

| Pull | Reality |
|---|---|
| "The whole bundle isn't done, so it's too early to cut issues" | The whole bundle is never done. Quiet is evaluated per subtree; waiting for the tree is waiting forever, and the bundle becomes the place design goes to continue forever. |
| "It went quiet, so I'll cut the issues" | Quiet triggers the *proposal*, nothing else. Promotion is joint, per backlog doctrine — cutting without the commitment conversation assumes the operator's yes. |
