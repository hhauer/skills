# Wayfinding: the design corpus and its discipline

Shared contract for `/agentic-sdlc:chart` and `/agentic-sdlc:survey` — the pre-spec design phase for initiative-sized work. An effort finds its way from a loose idea to a resolved design by answering one question at a time across many sessions, recording every decision in a corpus of markdown files. The finished corpus slices into backlog issues and feeds `the project's spec pipeline`; nothing is built from it directly.

## The corpus

One effort lives in one flat directory, `design/<effort>/`, on branch `design/<effort>` cut from main. The branch merges only via the effort's concluding pull request; an abandoned effort is a deleted branch. The corpus never lands on main mid-flight.

**The map owns all state; waypoint files own all content.** State appears in exactly one place — a waypoint's lifecycle is its name moving between map sections. Waypoint files carry no frontmatter and no status. There is no README, no central decisions file, no session log: the map is the only index, and each decision's one home is its waypoint.

### map.md

```markdown
# <Effort name>

## Destination

<What reaching the end looks like — the resolved design this effort is finding
its way to. One or two lines, always ending:>
Decisions locked; no code ships from this effort.

## Notes

<Domain context; skills every session should consult; standing preferences.>

## Frontier

- [waypoint-name](waypoint-name.md)

## Blocked

- [waypoint-name](waypoint-name.md) — waits on [other](other.md)

## Decisions so far

- [waypoint-name](waypoint-name.md) — <one-line gist of the answer>

## Not yet specified

<The fog — see below.>

## Out of scope

- <gist> — <why it sits past the destination>
```

Frontier and Blocked entries are bare linked names (plus waits-on edges). Never annotate them with progress prose — "narrowed", "partially decided", percent-done. That detail lives in the waypoint file; a reader who wants it zooms in.

### Waypoints

A waypoint is one question whose answer is one decision, sized to one session. If answering it would take two sittings, it is two waypoints; if it can't yet be phrased as a precisely-stated question, it is fog, not a waypoint.

```markdown
# <waypoint-name>

## Question

<The decision this waypoint resolves — sharp enough that a stranger could
tell whether a given answer settles it.>

## Decision

<Written at resolution: what was decided and why. The durable record.>
```

Four types, distinguished by content rather than metadata:

- **Decision** (the default) — resolved in conversation with the operator. Human-in-the-loop: the agent never stands in for the operator's side.
- **Research** — a fact the design waits on, findable in documentation, APIs, or primary sources. Resolved by a background agent that writes a `## Findings` section into the file, each claim cited. Dispatched the moment the waypoint exists; never blocks a session.
- **Prototype** — a cheap throwaway artifact built so the operator has something concrete to react to, when "how should this look/behave" is the question. The artifact lives on the effort branch, clearly marked throwaway, linked from the waypoint; the waypoint's Decision records the verdict, and only the verdict survives.
- **Task** — manual work that must happen before a decision can be made (provision access, sign up for a service, move data so its shape can be seen). The one type that *does* rather than decides; it earns its place by unblocking a decision. Records a `## Done` section: what happened, plus any facts later waypoints depend on.

## Fog of war

Chart only what you can see. Beyond the live waypoints lies the fog — decisions you can tell are coming but cannot yet pin down, written loosely into **Not yet specified**.

**Fog or waypoint? The test is whether the question can be stated precisely now — not whether it can be answered now.** A sharp question that's merely blocked is a waypoint under Blocked. A dim area ("something about billing, once gating resolves") is fog. Don't pre-slice fog into waypoint-sized pieces: one patch may graduate into several waypoints, or none, once the frontier reaches it.

## Out of scope

The destination fixes the scope; work past it is out of scope — not fog. It gets one gist line in **Out of scope** with the reason. Ruling something out is a **scoping act, and scoping acts are the operator's**: propose the ruling, get their yes, then move it. A waypoint revealed to sit past the destination is closed with a line here, not resolved.

## The conversation discipline

Sessions run on the operator's long, voice-dictated rambles. The unit of conversation is the ramble, not the question — but every session centers on one focus question that gives the ramble its center of gravity.

**Mine first.** When a ramble arrives, extract everything before responding: each decision stated or implied, each constraint, each new patch of fog, each scope musing, each contradiction with the recorded map.

**Then reply, in two moves:**

1. **Reflect back what the ramble settled**, as `decided X because Y` lines — the mirror the operator checks for misreadings. Challenges belong here too: a statement that contradicts a Decisions-so-far entry is called out immediately ("auth-provider decided Clerk; you just described minting our own sessions — which holds?"); a fuzzy boundary is stress-tested with a concrete edge-case scenario, not an abstract question.
2. **Pose the single most load-bearing question the ramble left open, with your recommended answer.** One question, in prose. Never AskUserQuestion — forced choices are the wrong shape for an operator who thinks by rambling.

**What may enter the record, and when:**

- A decision the operator stated in so many words: record it this session. The reflect-back is its audit; a misread is corrected on the spot.
- Anything you interpreted, inferred, or assumed — an ambiguous phrase read one way, a gap filled with a sensible default, an answer the stated mechanics merely *imply* ("re-send reissues the token, so reissue-or-expire must be the whole revocation story"): **not until they confirm**. Implication is still inference. When the Question names a part (revocation, say) that the ramble never addressed, that part is still open, however neatly the rest seems to cover it. A gap in the ramble is an open question, not a slot for your recommendation. The tell that you're crossing this line is opt-out framing — "I recorded X; say so if you want otherwise" is a decision you just made for them. The licensed form is "my read is X — confirm it and it goes in the record."
- A ramble that decisively settles a *different* frontier waypoint: reflect it explicitly ("this also resolves plan-gating — confirm?") and resolve it only on their yes. Spillover that informs without settling is written into that waypoint's file beneath its Question as context — a note in the chat is a note lost.
- Scope rulings, out-of-scope moves, and the effort's conclusion: always confirmed, never assumed.

Standing rules: facts findable in the environment are looked up, never asked. Decisions are always the operator's — recommend, then wait. Never answer your own question and proceed.

## Resolution bookkeeping

Resolving a waypoint changes the map around it. Every resolution, in order:

1. Write `## Decision` into the waypoint file — the what and the why.
2. Move its name to **Decisions so far** with a one-line gist.
3. **Sweep the map against the new answer.** Fog this answer sharpened graduates into waypoints (and leaves Not-yet-specified). Blocked waypoints whose last blocker just closed move to Frontier. Prose anywhere on the map that the answer made stale gets fixed. Waypoints the answer invalidated are amended or deleted; waypoints it revealed as past the destination are proposed for Out of scope.
4. Newly surfaced sharp questions become waypoint files, wired into Frontier or Blocked.
5. New research waypoints get their background agents dispatched before the session ends.
6. Commit and push the branch.

The sweep is not optional housekeeping — an unswept map lies about what's takeable, and the next session inherits the lie.
