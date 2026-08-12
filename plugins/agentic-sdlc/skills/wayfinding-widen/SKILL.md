---
name: wayfinding-widen
description: Use when a project's design bundle needs widening — a loose idea or region spanning many undecided questions, too big or too foggy for a single spec-writing session — including founding a project's first knowledge bundle under design/ and re-mapping a region after implementation reality diverged.
---

# Wayfinding: Widen

Widen the bundle: fan out breadth-first over one region of the project's design bundle, surfacing the open decisions as waypoints and fog that later `/agentic-sdlc:wayfinding-deepen` sessions resolve. Widening an empty `design/` founds the bundle — naming the root destination is the founding act; there is no separate bootstrap operation.

**REQUIRED BACKGROUND:** Read `${CLAUDE_PLUGIN_ROOT}/references/wayfinding.md` before anything else. It defines the OKF bundle, the map and node shapes, the frontmatter contract, the conversation discipline, and the fog rules this skill applies. Do not invent structure — no README, no central decisions file, no per-topic notes; the reference's shapes are the only ones widening produces.

## Flow

1. **Fix the region and its destination — in conversation, before any file changes.** On a founding session that means the root map's Destination: the project's north star, in the operator's terms — never process rules like the no-build invariant, which is doctrine, not map content — and the founding act also writes `design/index.md` (the `okf_version` pin) and fixes the operator's actor id in the root map's Notes. On an existing bundle it means naming where in the tree this widening lands and what resolved looks like for that subject. Reflect your understanding back and get the operator's yes — "set this up now" authorizes the edit, not a silent guess at the destination, and everything downstream inherits its scope.

2. **Fan out breadth-first, still in conversation.** Sweep the region shallowly — surface the open decisions, don't go deep on any one. Read before asking: the bundle itself, the codebase, specs, docs — and any pre-existing design material, which is environment to harvest, not a rival record. A prior design doc's still-live questions and confirmed decisions enter the bundle in the reference's shapes; what already drained into specs or code stays where it drained. **Escape hatch:** if the fan-out surfaces no fog — the way is already visible and the whole journey fits one session — say so and stop. No region for work that doesn't need one; ask the operator whether to take the small path instead (plan mode, or straight to `the project's spec pipeline`).

3. **Write the map edits.** Cut a working branch from main (or continue the previous session's branch if it hasn't merged yet). Write or extend maps per the reference's node shapes — a subject earns its directory with its first waypoint. For each question sharp enough to state precisely, a waypoint — **one question, one decision, one session's size.** A waypoint that names an *area* ("metering and aggregation") rather than a *decision* ("what is the billable event?") is mis-sized: find the first sharp question inside it and leave the rest as fog. Everything not yet stateable goes to the owning map's Not-yet-specified as loose prose. Wire Frontier and Blocked; Out of scope holds only exclusions the operator has actually ruled. Stamp `generated` on everything you write.

4. **Dispatch background agents.** Every research waypoint gets `agentic-sdlc:waypoint-researcher` launched now, in parallel — pass each agent its waypoint's path; the waypoint's Question is its brief and the reference's sources-and-footnotes contract is its output shape. Every Prototype waypoint gets `agentic-sdlc:waypoint-prototyper` the same way — its build brief must already sit beneath the Question, written in conversation before dispatch. Neither blocks the session; whatever lands after the session ends waits uncommitted for the next sweep.

5. **Lint, commit, land the branch, stop.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint_bundle.py" design/` and fix every finding first. Then ask the operator to land the session on main — **their typed yes is the approval**; fast-forward merge, push, delete the branch, per the reference's version-control contract. If they defer, push the branch and stop; a PR exists only if they ask for one. Report the region's shape: destination, frontier, what's in the fog, what research is running.

## Widening resolves nothing

The widening session's entire output is map. Every question stays open — including the ones you could answer right now.

| Pull | Reality |
|---|---|
| "This one's obvious, I'll just record the answer" | Obvious answers are cheap to confirm in a deepening session — and wrong obvious answers poison the map. Map it; don't answer it. |
| "The operator already implied the answer while describing the idea" | An aside inside an idea-ramble is not a worked decision. Put what they said beneath the waypoint's Question as context; resolve it in a deepening session. |
| "It's inefficient to end without resolving anything" | Widening's product is the map. A good map makes twenty later sessions efficient; one smuggled resolution makes none of them trustworthy. |
| "I'll sketch the likely design in the fog section" | Fog is for *questions* you can't sharpen yet, not answers you're eager to give. Designs live in Decisions, which widening never writes. |
