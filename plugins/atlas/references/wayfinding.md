# Wayfinding: the design bundle and its discipline

Shared contract for `/atlas:widen` and `/atlas:deepen` — the pre-spec design phase. A project's design intent lives in one permanent **knowledge bundle**: a corpus of markdown maps and waypoints at `design/`, on main, conforming to the [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/SPEC.md). A widening session fans out breadth-first over one region, producing waypoints and fog, resolving nothing. A deepening session resolves one waypoint depth-first, with the operator. Both are map operations on the same bundle; neither opens an effort and neither concludes one. Quiet regions slice into backlog issues; nothing is built from the bundle directly.

## The bundle

One project, one design bundle, permanent. On disk it is OKF: every file is a **concept** — YAML frontmatter, then a markdown body. The root is `design/map.md`, a map like any other, beside a static `design/index.md` that pins the format version. The tree is organized by **subject, not by when the work happened**: in two years nobody cares which month the disciplines were worked through; they care where discipline design lives. A level exists only when the level above it grew too wide to read — depth is discovered, never scaffolded in advance.

The root map's Destination is the project's north star; every other map's Destination says only what resolved looks like for its own subject. *No code ships from the bundle* is a project-wide invariant, but it is doctrine — this contract, which every session reads — not map content: a Destination describes the project, and writing process rules into it pollutes the north star with machinery.

Sessions land through version control like all other work: each session runs on an ordinary working branch cut from main — or continues the previous session's branch if it hasn't merged yet, rather than stacking a second. At session close, ask the operator to land the branch; **their typed yes in conversation is the approval** (per the version-control rules — a selection in a tool prompt doesn't count), and on it the session fast-forward merges to main (rebasing onto main first if it has moved), pushes, and deletes the branch. If the operator defers, push the branch and stop — it waits unmerged for the next session; a pull request is cut only if the operator asks for one, e.g. to read a founding widen's whole bundle cold before it becomes truth. The bundle on main is the readable truth, so land promptly — but main moves only on that typed approval.

### The OKF substrate

`design/index.md` is written once at founding and stays a static pointer — it never enumerates concepts (Regions owns that, and a listing here would be a second home to drift):

```markdown
---
okf_version: "0.2"
---

# Design bundle

* [Root map](map.md) - start here
```

Upgrading the pinned version is a deliberate, operator-approved act — never a side effect of a session.

**State lives in maps; trust lives in frontmatter.** A waypoint's lifecycle is its name moving between the sections of the map directly above it — frontmatter never carries OKF `status`, progress notes, or lifecycle state. Frontmatter carries what the maps never did: who wrote a thing and who confirmed it.

- `type` — required on every concept: `Map`, `Decision`, `Research`, `Prototype`, or `Task`.
- `generated: { by: <actor>, at: <ISO 8601> }` — stamped by whoever writes or meaningfully rewrites the concept.
- `verified` — confirmation events, each `{ by: <actor>, at: <ISO 8601> }`. **A `human:` entry here is what makes a recorded Decision legitimate**; the operator's confirmation in conversation is the verification event, and the session stamps it when it writes the Decision. No confirmation, no stamp — and no Decision text.
- `sources` — provenance on research findings; see the Research waypoint type.

Actors follow the OKF convention: `human:<id>` for the operator, `<producer>/<model>` for agents (e.g. `claude-code/claude-fable-5`, `waypoint-researcher/claude-fable-5`). The operator's actor id is fixed at founding — derived from their forge username unless they say otherwise — and recorded in the root map's Notes, so every later session stamps the same id. Timestamps come from `date -u`, never from memory.

Run the format lint before every commit; findings are fixed, not shipped:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint_bundle.py" design/
```

## Maps and node shapes

A node takes one of two shapes:

- **Map** — a directory's `map.md`, `type: Map`. The map half of every subject.
- **Waypoint file** — one file per waypoint, `type: Decision | Research | Prototype | Task`, holding `# <name>`, `## Question`, and its resolution section.

A subject earns a directory the moment it has its first waypoint: `<subject>/map.md` plus waypoint files beside it. A subject with no waypoint yet — visible but not yet mappable — is a fog line in its parent's Not yet specified, not a file. There is no intermediate page shape: a waypoint is an OKF concept, and a concept's trust lives in its own frontmatter, so waypoints are files from birth.

Every map, at every level, has the same skeleton (empty sections omitted):

```markdown
---
type: Map
generated: { by: claude-code/<model>, at: 2026-08-09T18:00:00Z }
---

# <Subject>

## Destination

<What resolved looks like for this subject; at the root, the project's north star.>

## Notes

<Domain context; skills every session should consult; standing preferences.
At the root: the operator's actor id.>

## Regions

- [child-subject](child-subject/map.md)

## Frontier

- [waypoint-name](waypoint-name.md)

## Blocked

- [waypoint-name](waypoint-name.md) — waits on [other](other.md)

## Decisions so far

- [waypoint-name](waypoint-name.md) — <one-line gist of the answer>

## Not yet specified

<The fog — see below.>

## Out of scope

- <gist> — <why it sits past this map's destination>

## Issues cut

<Absent until commitment — see Quiet subtrees below.>
```

**Regions and Frontier list children as bare links — never with a status annotation.** No "mostly done", no "quiet", no progress prose. A parent that records nothing about a child's state has nothing that can drift; whether a subtree is quiet is discovered by reading it, never recorded above it.

### Waypoints

A waypoint is one question whose answer is one decision, sized to one session. If answering it would take two sittings, it is two waypoints; if it can't yet be phrased as a precisely-stated question, it is fog, not a waypoint.

Four types, declared in frontmatter:

- **Decision** (the default) — resolved in conversation with the operator. Human-in-the-loop: the agent never stands in for the operator's side. Its `## Decision` is written only alongside a `verified: { by: human:<id>, at: … }` stamp.
- **Research** — a fact the design waits on, findable in documentation, APIs, or primary sources. Resolved by the `atlas:waypoint-researcher` agent, which writes a `## Findings` section plus `sources` frontmatter, each claim carrying a footnote keyed to a source id:

  ```markdown
  ---
  type: Research
  generated: { by: waypoint-researcher/<model>, at: 2026-08-09T18:40:00Z }
  sources:
    - id: stripe-metering
      resource: https://docs.stripe.com/billing/subscriptions/usage-based
      title: Stripe usage-based billing
  ---

  # billable-event

  ## Question

  What is the billable event?

  ## Findings

  Stripe meters usage per event record.[^stripe-metering]

  [^stripe-metering]: Stripe usage-based billing
  ```

  Dispatched the moment the waypoint exists; never blocks a session. The researcher writes into the working tree; the session commits whatever has landed by the time it ends, and findings that land after the last commit sit uncommitted on the branch until the next session's sweep commits them.
- **Prototype** — a cheap throwaway artifact built so the operator has something concrete to see and operate, when "how should this look/behave" is the question. The session writes the build brief in conversation with the operator, as prose beneath the `## Question` — what to roughly build, what interaction the operator needs to have with it. Built by the `atlas:waypoint-prototyper` agent, dispatched the moment the waypoint exists — cutting the waypoint together is the consent; there is no separate build gate. The agent builds into `<waypoint-name>.prototype/` beside the waypoint (a directory the bundle lint skips by that exact suffix), under a deliberate ceremony exemption — no TDD, no review; its one quality bar is that the artifact runs — and writes one section back, `## Artifact`: how to run the thing and what to look at. It never writes the `## Decision`. The operator reacts in a session — the dispatching one or a later deepen; the background agent is a builder the operator never talks to. The verdict lands as the `## Decision` (with the operator's `verified` stamp, like any decision), and only the verdict survives: recording it is also the moment the artifact dies — delete the `.prototype/` directory and the `## Artifact` section with it. The bundle is mutable and git keeps the corpse. A prototype is sized to one agent run; a brief the agent reports back as too big is reshaped into smaller waypoints, not built anyway.
- **Task** — manual work that must happen before a decision can be made (provision access, sign up for a service, move data so its shape can be seen). The one type that *does* rather than decides; its `## Question` names what it unblocks, and it records a `## Done` section: what happened, plus any facts later waypoints depend on.

## Fog of war

Map only what you can see. Beyond the live waypoints lies the fog — decisions you can tell are coming but cannot yet pin down, written loosely into the **Not yet specified** of whichever map they belong to.

**Fog or waypoint? The test is whether the question can be stated precisely now — not whether it can be answered now.** A sharp question that's merely blocked is a waypoint under Blocked. A dim area ("something about billing, once gating resolves") is fog. Don't pre-slice fog into waypoint-sized pieces: one patch may graduate into several waypoints, or none, once the frontier reaches it.

## Out of scope

Each map's destination fixes its scope; work past it is out of scope — not fog. It gets one gist line in **Out of scope** with the reason. Ruling something out is a **scoping act, and scoping acts are the operator's**: propose the ruling, get their yes, then move it. A waypoint revealed to sit past the destination is closed with a line here, not resolved. Abandoning a whole direction works the same way — its files move under Out of scope with their reasoning intact. An edit keeps the why; there is no deleted branch to lose it.

## The bundle is mutable — and the why is load-bearing

The bundle is **not a verification contract**. OpenSpec's records are immutable because shipped code is checked against them; the design bundle is checked against nothing. It is the design north star, co-mutated — edited deliberately and jointly, the way any high-ranking single source of truth is. Corrections happen in place, not in appendices; closing a question has never precluded reopening it.

Mutability is what makes the why mandatory. A future editor reading `decided X` with no stated reason cannot tell whether the reason still holds, and will either preserve the decision superstitiously or overwrite it carelessly. Git history technically holds the ramble; nobody reads git history for design rationale. So:

**A Decision enters the record only with its why, and the why is the operator's — stated by them, or proposed by you and confirmed by them.** The `verified` stamp records that the confirmation happened; the Decision's prose records the why itself. No why, no record. This holds under every pressure:

- "Log it and move on" is not a why. The licensed move costs one sentence: *"Recording it needs the because — one sentence?"* An operator three hours in can produce a reason in less time than it takes to flag its absence.
- Do not record the decision with the rationale slot blank or "flagged for later." A why-less entry is not a safe placeholder — it is exactly the unsafe page mutability forbids, and later never comes.
- Do not draft a plausible rationale and record it flagged as inference, promising it's cheap to fix. That is your reasoning laundered into the operator's record, wrapped in the opt-out framing the conversation discipline already bans. Propose the why aloud, get the yes, then write it.
- Do not stamp `verified` with the operator's actor on your own authority — the stamp asserts their confirmation happened in conversation, and a fabricated stamp is a forged signature on a record built to be trusted. (The lint catches a Decision with no human stamp; only the discipline prevents a false one.)
- Refusing to write is not holding the session hostage; it is one reflected question. The decision stays in the conversation, loses nothing, and lands the moment the reason exists.

Editing an existing Decision follows the same rule: the new text carries the new why, a fresh `generated` stamp, and a fresh confirmation.

## The conversation discipline

Sessions run on the operator's long, voice-dictated rambles. The unit of conversation is the ramble, not the question — but every session centers on one focus question that gives the ramble its center of gravity.

**Mine first.** When a ramble arrives, extract everything before responding: each decision stated or implied, each constraint, each new patch of fog, each scope musing, each contradiction with the recorded map.

**Then reply, in two moves:**

1. **Reflect back what the ramble settled**, as `decided X because Y` lines — the mirror the operator checks for misreadings. Challenges belong here too: a statement that contradicts a Decisions-so-far entry is called out immediately ("auth-provider decided Clerk; you just described minting our own sessions — which holds?"); a fuzzy boundary is stress-tested with a concrete edge-case scenario, not an abstract question.
2. **Pose the single most load-bearing question the ramble left open, with your recommended answer.** One question, in prose. Never AskUserQuestion — forced choices are the wrong shape for an operator who thinks by rambling.

**What may enter the record, and when:**

- A decision the operator stated in so many words — with its why: record it this session. The reflect-back is its audit; a misread is corrected on the spot.
- Anything you interpreted, inferred, or assumed — an ambiguous phrase read one way, a gap filled with a sensible default, an answer the stated mechanics merely *imply* ("re-send reissues the token, so reissue-or-expire must be the whole revocation story"): **not until they confirm**. Implication is still inference. When the Question names a part (revocation, say) that the ramble never addressed, that part is still open, however neatly the rest seems to cover it. A gap in the ramble is an open question, not a slot for your recommendation. The tell that you're crossing this line is opt-out framing — "I recorded X; say so if you want otherwise" is a decision you just made for them. The licensed form is "my read is X — confirm it and it goes in the record."
- A ramble that decisively settles a *different* frontier waypoint: reflect it explicitly ("this also resolves plan-gating — confirm?") and resolve it only on their yes. Spillover that informs without settling is written into that waypoint's file beneath its Question as context — a note in the chat is a note lost.
- Scope rulings, out-of-scope moves, and cutting a quiet subtree's issues: always confirmed, never assumed.

Standing rules: facts findable in the environment are looked up, never asked. Decisions are always the operator's — recommend, then wait. Never answer your own question and proceed.

## Resolution bookkeeping

Resolving a waypoint changes the map around it. Every resolution, in order:

1. Write `## Decision` into the waypoint — the what and the why, per the mutability rule above — and stamp `verified` with the operator's actor and the confirmation time. For a Prototype waypoint this is also when the artifact dies: delete its `.prototype/` directory and its `## Artifact` section — only the verdict survives.
2. Move its name to **Decisions so far** in its nearest enclosing map, with a one-line gist.
3. **Sweep the map against the new answer.** Fog this answer sharpened graduates into waypoints (and leaves Not-yet-specified). Blocked waypoints whose last blocker just closed move to Frontier. Prose anywhere the answer made stale gets fixed — in this map or any other; the bundle is mutable. Waypoints the answer invalidated are amended or deleted; waypoints it revealed as past the destination are proposed for Out of scope.
4. Newly surfaced sharp questions become waypoints, wired into Frontier or Blocked.
5. New research waypoints get `atlas:waypoint-researcher` dispatched before the session ends; new Prototype waypoints — brief written beneath the Question first — get `atlas:waypoint-prototyper` the same way.
6. **Check for quiet.** Walk up from the resolved waypoint's map toward the root; if the sweep left any subtree quiet, propose the commitment conversation for the highest quiet node (see below).
7. Run the lint, fix what it finds, commit, and land the branch per the version-control contract above.

The sweep is not optional housekeeping — an unswept map lies about what's takeable, and the next session inherits the lie.

## Quiet subtrees — where issues get cut

A permanent bundle never runs out: there is always another open question somewhere. The unit that finishes is the **subtree**. A subtree is **quiet** when its map and every map beneath it have an empty Frontier, an empty Blocked, and nothing in Not yet specified. A quiet subtree is what an effort used to be — discovered at whatever size the design actually resolved, not declared in advance.

When bookkeeping finds a quiet subtree, **propose the commitment conversation there and then** — proposing is the session's job, deciding is the operator's: hold it now, or park it and keep deepening elsewhere. A parked proposal is re-raised next time the subtree is touched; it is never queued in a file — a "ready to cut" list is state the maps don't own.

The commitment conversation, when the operator takes it:

1. **Slice.** Propose how the subtree's resolved design divides into backlog issues — how many changes, what order, what depends on what. A quiet subtree cuts alone; it never waits for siblings.
2. **Promote.** Which slices are committed work and which are drafts is the operator's call, made here — never assumed from quietness.

**The bundle's part ends there.** Filing the issues, and writing the map's `## Issues cut` section afterward, belong to whatever backlog tool the project uses — the bundle owns the slice and the slot, not the filing. The slot's contract holds regardless of who writes it: an ordered list, in build order, of issue links with one-line gists. **Cross-issue ordering lives in that section and nowhere else**, because issue trackers generally cannot express dependency between issues; a map that omits the order loses it for good.

The arrow runs one way: **bundle → issues → build**. Backlog issues are never an input to a widening, and design work is never filed as an issue. There is no back-feed from implementation either — when building collides with reality, the next widening's fan-out reads the specs and code like any other part of the environment and re-fogs what changed. A cut subtree that later reopens is just a subtree with new fog; the bundle is mutable.
