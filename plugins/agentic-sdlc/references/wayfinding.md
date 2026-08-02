# Wayfinding: the design atlas and its discipline

Shared contract for `/agentic-sdlc:chart` and `/agentic-sdlc:survey` — the pre-spec design phase. A project's design intent lives in one permanent **atlas**: a recursive corpus of markdown maps at `design/`, on main. Chart **widens** it — a breadth-first fan-out over one region, producing waypoints and fog, resolving nothing. Survey **deepens** it — depth-first resolution of one waypoint, with the operator. Both are map operations on the same atlas; neither opens an effort and neither concludes one. Quiet regions slice into backlog issues and feed `the project's spec pipeline`; nothing is built from the atlas directly.

## The atlas

One project, one atlas, permanent. "Atlas" is a spoken word — on disk there are only maps, and the root is `design/map.md`, a map like any other. The tree is organized by **subject, not by when the work happened**: in two years nobody cares which month the disciplines were surveyed; they care where discipline design lives. A level exists only when the level above it grew too wide to read — depth is discovered, never scaffolded in advance.

The root map's Destination is the project's north star, and it always ends: *No code ships from the atlas.* That invariant is project-wide; every other map's Destination says only what resolved looks like for its own subject.

Sessions land through version control like all other work: each session runs on an ordinary working branch cut from main and ends with a pull request the operator merges. If the previous session's PR is still open, continue on that branch rather than stacking a second. The atlas on main is the readable truth; no session touches main directly.

## Maps and node shapes

**State lives in the nearest enclosing map — and nowhere else.** A waypoint's lifecycle is its name moving between the sections of the map directly above it: the `map.md` beside a waypoint file, or the map half of the page a waypoint section lives in. Waypoints carry no frontmatter and no status. There is no README, no central decisions file, no session log.

Every map, at every level, has the same skeleton:

```markdown
# <Subject>

## Destination

<What resolved looks like for this subject. At the root only, always ending:>
No code ships from the atlas.

## Notes

<Domain context; skills every session should consult; standing preferences.>

## Regions

- [child-subject](child-subject.md)
- [child-directory](child-directory/map.md)

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

**Regions lists children as bare links — never with a status annotation.** The same rule Frontier entries carry: no "mostly done", no "quiet", no progress prose. A parent that records nothing about a child's state has nothing that can drift; whether a subtree is quiet is discovered by reading it, never recorded above it. Empty sections are omitted.

A node takes one of three shapes, and grows from one to the next:

- **Leaf waypoint file** — `# name`, `## Question`, `## Decision`. Listed in its directory's `map.md` state sections.
- **Subject page** — a subject that hasn't earned a directory is one file: the map skeleton on top, then a `---` divider, then its waypoints as `## <waypoint-name>` sections each holding `### Question` and `### Decision`. Everything above the divider is the map; everything below is waypoint content. State links point at anchors: `[test-of-the-plow](#test-of-the-plow)`. The page is listed in its parent's Regions.
- **Directory** — a subject too wide for one page: `<subject>/map.md` plus children (waypoint files, subject pages, subdirectories).

When a page grows too wide to read, split it: its map half becomes `<subject>/map.md`, its waypoint sections become files. The split is an ordinary edit made during bookkeeping, not a ceremony.

### Waypoints

A waypoint is one question whose answer is one decision, sized to one session. If answering it would take two sittings, it is two waypoints; if it can't yet be phrased as a precisely-stated question, it is fog, not a waypoint.

Four types, distinguished by content rather than metadata:

- **Decision** (the default) — resolved in conversation with the operator. Human-in-the-loop: the agent never stands in for the operator's side.
- **Research** — a fact the design waits on, findable in documentation, APIs, or primary sources. Resolved by a background agent that writes a `## Findings` section into the file, each claim cited. Dispatched the moment the waypoint exists; never blocks a session.
- **Prototype** — a cheap throwaway artifact built so the operator has something concrete to react to, when "how should this look/behave" is the question. The artifact lives beside the waypoint, clearly marked throwaway; the Decision records the verdict, and only the verdict survives — once it does, delete the artifact. The atlas is mutable and git keeps the corpse.
- **Task** — manual work that must happen before a decision can be made (provision access, sign up for a service, move data so its shape can be seen). The one type that *does* rather than decides; it earns its place by unblocking a decision. Records a `## Done` section: what happened, plus any facts later waypoints depend on.

## Fog of war

Chart only what you can see. Beyond the live waypoints lies the fog — decisions you can tell are coming but cannot yet pin down, written loosely into the **Not yet specified** of whichever map they belong to.

**Fog or waypoint? The test is whether the question can be stated precisely now — not whether it can be answered now.** A sharp question that's merely blocked is a waypoint under Blocked. A dim area ("something about billing, once gating resolves") is fog. Don't pre-slice fog into waypoint-sized pieces: one patch may graduate into several waypoints, or none, once the frontier reaches it.

## Out of scope

Each map's destination fixes its scope; work past it is out of scope — not fog. It gets one gist line in **Out of scope** with the reason. Ruling something out is a **scoping act, and scoping acts are the operator's**: propose the ruling, get their yes, then move it. A waypoint revealed to sit past the destination is closed with a line here, not resolved. Abandoning a whole direction works the same way — its pages move under Out of scope with their reasoning intact. An edit keeps the why; there is no deleted branch to lose it.

## The atlas is mutable — and the why is load-bearing

The atlas is **not a verification contract**. OpenSpec's records are immutable because shipped code is checked against them; the atlas is checked against nothing. It is the design north star, co-mutated — edited deliberately and jointly, the way any high-ranking single source of truth is. Corrections happen in place, not in appendices; closing a question has never precluded reopening it.

Mutability is what makes the why mandatory. A future editor reading `decided X` with no stated reason cannot tell whether the reason still holds, and will either preserve the decision superstitiously or overwrite it carelessly. Git history technically holds the ramble; nobody reads git history for design rationale. So:

**A Decision enters the record only with its why, and the why is the operator's — stated by them, or proposed by you and confirmed by them.** No why, no record. This holds under every pressure:

- "Log it and move on" is not a why. The licensed move costs one sentence: *"Recording it needs the because — one sentence?"* An operator three hours in can produce a reason in less time than it takes to flag its absence.
- Do not record the decision with the rationale slot blank or "flagged for later." A why-less entry is not a safe placeholder — it is exactly the unsafe page mutability forbids, and later never comes.
- Do not draft a plausible rationale and record it flagged as inference, promising it's cheap to fix. That is your reasoning laundered into the operator's record, wrapped in the opt-out framing the conversation discipline already bans. Propose the why aloud, get the yes, then write it.
- Refusing to write is not holding the session hostage; it is one reflected question. The decision stays in the conversation, loses nothing, and lands the moment the reason exists.

Editing an existing Decision follows the same rule: the new text carries the new why.

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

1. Write `## Decision` into the waypoint — the what and the why, per the mutability rule above.
2. Move its name to **Decisions so far** in its nearest enclosing map, with a one-line gist.
3. **Sweep the map against the new answer.** Fog this answer sharpened graduates into waypoints (and leaves Not-yet-specified). Blocked waypoints whose last blocker just closed move to Frontier. Prose anywhere the answer made stale gets fixed — in this map or any other; the atlas is mutable. Waypoints the answer invalidated are amended or deleted; waypoints it revealed as past the destination are proposed for Out of scope.
4. Newly surfaced sharp questions become waypoints, wired into Frontier or Blocked.
5. New research waypoints get their background agents dispatched before the session ends.
6. **Check for quiet.** Walk up from the resolved waypoint's map toward the root; if the sweep left any subtree quiet, propose the commitment conversation for the highest quiet node (see below).
7. Commit, push, and make sure the session's pull request exists.

The sweep is not optional housekeeping — an unswept map lies about what's takeable, and the next session inherits the lie.

## Quiet subtrees — where issues get cut

A permanent atlas never runs out: there is always another open question somewhere. The unit that finishes is the **subtree**. A subtree is **quiet** when its map and every map beneath it have an empty Frontier, an empty Blocked, and nothing in Not yet specified. A quiet subtree is what an effort used to be — discovered at whatever size the design actually resolved, not declared in advance.

When bookkeeping finds a quiet subtree, **propose the commitment conversation there and then** — proposing is the session's job, deciding is the operator's: hold it now, or park it and keep surveying elsewhere. A parked proposal is re-raised next time the subtree is touched; it is never queued in a file — a "ready to cut" list is state the maps don't own.

The commitment conversation, when the operator takes it:

1. **Slice.** Propose how the subtree's resolved design divides into backlog issues — how many changes, what order, what depends on what. A quiet subtree cuts alone; it never waits for siblings.
2. **Promote.** Which slices are committed work (`state/approved` + `flow/*` lane) and which are drafts is the operator's call, made here, per the backlog doctrine — never assumed from quietness.
3. **Cut** the issues with the `dev-tools:fj` skill. Each issue body links the subtree's map by path so later spec-writing sessions mine the atlas.
4. **Record.** Write `## Issues cut` into the subtree's map: an ordered list — build order — of issue links with one-line gists. Ordering lives here and only here; Forgejo cannot express cross-issue dependency, so the map is its one home.

The arrow runs one way: **atlas → issues → propose**. Backlog issues are never an input to a chart, and design work is never filed as an issue. There is no back-feed from implementation either — when building collides with reality, the next chart's fan-out reads the specs and code like any other part of the environment and re-fogs what changed. A cut subtree that later reopens is just a subtree with new fog; the atlas is mutable.
