---
name: wayfinder
description: Use when a project's design bundle under design/ needs work — founding the bundle, widening over a loose idea or region too big or too foggy for one spec-and-build cycle, resolving an open waypoint with the operator, sweeping landed research onto the maps, or re-mapping a region after implementation reality diverged. One skill for both motions; it reads the bundle and chooses widen or deepen itself.
---

# Wayfinder

Tend the project's design bundle: fan out over foggy regions (widen) and resolve waypoints with the operator (deepen). Both are map operations on one permanent bundle at `design/`, and a session moves between them as the work demands.

**REQUIRED BACKGROUND:** Read `${CLAUDE_PLUGIN_ROOT}/references/wayfinding.md` before anything else. It defines the OKF bundle, the map and node shapes, the frontmatter trust contract, the conversation discipline, the mutability rule, the fog rules, and the resolution bookkeeping. This file is the flow around them. Do not invent structure — no README, no central decisions file, no per-topic notes; the reference's shapes are the only ones a session produces.

## Read the bundle, then choose the motion

Start by reading `design/`: absent, or present with its root map and the maps on the path from the root to whatever region the operator named. Load maps, not waypoints — zoom into individual waypoints on demand during conversation.

Then choose the motion from the bundle's state and what the operator brought. **Widen** when there is no `design/` yet (founding), when the operator arrives with a loose idea or a region spanning undecided questions, or when implementation reality has diverged from a mapped region. **Deepen** when the operator names a waypoint, when the frontier holds landed research Findings or a ripe Prototype Artifact to sweep, or when any concept carries an open `## Challenge`. The choice is silent — go straight into the motion. What is never silent is what the motions already reflect back: a widen states the region's destination for the operator's yes before writing anything; a deepen names its recommended focus and why.

**Motions alternate within a session.** A deepen's bookkeeping widens a little every time it cuts newly sharp waypoints or re-fogs; when an answer uncovers a region too foggy to bookkeep in passing, fan out over it properly. A widen never writes a Decision — when the operator turns to something the fan-out surfaced and asks to settle it now, switch to deepen for that one waypoint: fix it as the focus, run the resolution discipline in full, stamp, bookkeep, then return to fanning out. The switch is a request the operator makes deliberately, and it buys none of the discipline's exemptions: an answer dropped in passing while they describe the region is not that request, "that's a given" is not a why, and the waypoint keeps what they said as context beneath its Question until they resolve it properly.

## Shared flow

1. **Branch.** Cut a working branch from main, or continue the previous session's branch if it hasn't merged yet — never stack a second.
2. **Work the motion** (below), committing as bookkeeping completes. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint_bundle.py" design/` before every commit and fix every finding first.
3. **Dispatch background agents as waypoints appear.** Every new Research waypoint gets `atlas:waypoint-researcher`; every new Prototype waypoint gets `atlas:waypoint-prototyper`, its build brief already written beneath the Question in conversation. Plain **unnamed** background Agent calls — never pass `name`; a named (teammate) dispatch silently loses the agent's report. Pass each agent its waypoint's path. Neither blocks the session; whatever lands after the session ends waits uncommitted for the next sweep.
4. **The session continues until the operator ends it.** A resolved focus or a finished fan-out is the middle of a session, not its end: recommend the next most load-bearing frontier waypoint, or follow the operator wherever they go next. Never propose landing because bookkeeping finished — session close is the operator's signal, not yours to infer.
5. **At the operator's session close: dispatch the auditor, then land.** If the session wrote or amended any concept, dispatch `atlas:wayfinding-auditor` — unnamed, like step 3 — with the bundle root and every concept touched; its challenges land whenever they land, swept by the next session. Then ask the operator to land the session on main — **their typed yes is the approval**; fast-forward merge, push, delete the branch, per the reference's version-control contract. If they defer, push the branch and stop; a PR exists only if they ask for one. Report the bundle's shape: destination, frontier, what's in the fog, what research is running.

## Widen

Fan out breadth-first over one region, surfacing the open decisions as waypoints and fog. The widen's entire output is map.

1. **Fix the region and its destination — in conversation, before any file changes.** On a founding session that means the root map's Destination: the project's north star, in the operator's terms — never process rules like the no-build invariant, which is doctrine, not map content — and the founding act also writes `design/index.md` (the `okf_version` pin) and fixes the operator's actor id in the root map's Notes. On an existing bundle it means naming where in the tree this widening lands and what resolved looks like for that subject. Reflect your understanding back and get the operator's yes — "set this up now" authorizes the edit, not a silent guess at the destination, and everything downstream inherits its scope.

2. **Fan out, still in conversation.** Sweep the region shallowly — surface the open decisions, don't go deep on any one. Read before asking: the bundle, the codebase, specs, docs — and any pre-existing design material, which is environment to harvest, not a rival record. A prior design doc's still-live questions and confirmed decisions enter the bundle in the reference's shapes; what already drained into specs or code stays where it drained. **Escape hatch:** if the fan-out surfaces no fog — the way is already visible and the whole journey fits one session — say so and stop. No region for work that doesn't need one; ask the operator whether to take the small path instead — plan it and build it directly, with no region at all.

3. **Write the map edits.** Write or extend maps per the reference's node shapes — a subject earns its directory with its first waypoint. For each question sharp enough to state precisely, a waypoint — **one question, one decision, one session's size.** A waypoint that names an *area* ("metering and aggregation") rather than a *decision* ("what is the billable event?") is mis-sized: find the first sharp question inside it and leave the rest as fog. A question that has crossed into implementation — phrased against the shipped code rather than against what the project is — is neither waypoint nor fog: it goes to the map's Handed off as one gist line, per the reference, even when the operator asks for it on the map; reflect the handoff back and let them sharpen it into a play question if it is one. Everything not yet stateable goes to the owning map's Not-yet-specified as loose prose. Wire Frontier and Blocked; Out of scope holds only exclusions the operator has actually ruled. Stamp `generated` on everything you write. Then lint, commit, and dispatch per the shared flow.

### Widening resolves nothing

Every question the fan-out surfaces stays open — including the ones you could answer right now.

| Pull | Reality |
|---|---|
| "This one's obvious, I'll just record the answer" | Obvious answers are cheap to confirm in the deepen motion — and wrong obvious answers poison the map. Map it; don't answer it. |
| "The operator already implied the answer while describing the idea" | An aside inside an idea-ramble is not a worked decision. Put what they said beneath the waypoint's Question as context; resolve it as a deepen, focus fixed, why stated. |
| "It's inefficient to end without resolving anything" | Widening's product is the map. A good map makes twenty later resolutions efficient; one smuggled resolution makes none of them trustworthy. |
| "I'll sketch the likely design in the fog section" | Fog is for *questions* you can't sharpen yet, not answers you're eager to give. Designs live in Decisions, which the widen motion never writes. |
| "The what is settled; the interesting question is how the code should take it" | Then the map is done with it. A question about code shape is a handoff to the spec that builds it, not a waypoint — hold it and the next reader takes settled design for open design. |

## Deepen

Resolve the focus waypoint with the operator and keep the maps honest.

1. **Sweep landed agent work.** Any research waypoint whose `## Findings` arrived since the last session — including findings sitting uncommitted on the branch from agents that outlived their session: gist it onto its map (Decisions so far) and run the reference's resolution bookkeeping before new work starts. A Prototype waypoint whose `## Artifact` has landed is different: it is *ripe, not resolved* — commit it, leave it on the Frontier, and surface it when recommending a focus; the operator reacting to the artifact is what resolves it. Any open `## Challenge` the auditor left — on any concept — is surfaced to the operator this session: they re-affirm the challenged text (delete the section) or amend it per the reference's mutability rule. A challenge is never closed without them.

2. **Fix the focus.** The operator usually arrives with a waypoint picked. If they don't name one, recommend the frontier waypoint you judge most load-bearing — the one whose answer unblocks or reshapes the most — and say why. The session centers on its Question.

3. **Resolve it** by the reference's conversation discipline: mine the ramble, reflect back `decided X because Y`, challenge contradictions against the map, pose one question with a recommendation. Record only what the discipline licenses — stated decisions with their why, interpretations and spillover on confirmation, gaps never. **No why, no record:** a decision whose reason wasn't stated or confirmed stays in the conversation until it is — and the recorded Decision carries the operator's `verified` stamp, which asserts that confirmation happened. The reference's mutability section owns both rules.

4. **Bookkeep** per the reference: Decision and stamp into the waypoint (for a Prototype, that's also when the artifact and its `## Artifact` section are deleted), gist onto its map, sweep fog/blocked/stale prose, cut newly-sharp waypoints and dispatch their agents per the shared flow — and hand off, rather than cut, any question that has crossed into code shape, including a frontier waypoint the answer reveals as one. Then lint, commit, recommend the next focus, and return to step 2 — the session continues until the operator ends it.

### The pull to build

Somewhere along the way a resolved waypoint will look like ten minutes of code, and the operator may say "just set it up while we're here." **The pull to do the work is the signal you've reached the map's edge, not permission to cross it.** The doctrine's project-wide invariant — no code ships from the bundle — is the standing rule; building from a design branch buries a feature where no verifier, spec, or reviewer will ever meet it.

Record the decision, then say where the build actually lands: a slice in a later backlog issue, or — if the operator genuinely wants it today — its own change through the normal pipeline, started outside the bundle. That costs one sentence now and keeps the bundle a design record instead of a half-shipped branch.
