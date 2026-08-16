# The docs bundle: doctrine for documenting a system as built

You are working on a **docs bundle**: a system's as-built documentation as a
corpus of markdown concepts at `docs/`, on main, conforming to the
[Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/SPEC.md).
The `document` skill defines how a run proceeds; the four phase agents
(enumerator, scribe, synthesizer, verifier) each carry their own operating
contract. What follows are the rules they all share and the reasons those
rules bind — consult it when a boundary call isn't settled by your own brief.

## Two corpora, one substrate

A project carries up to two knowledge bundles, and they are never one folder:

- **`design/`** — as-designed: what *ought* to be built. Stateful maps and
  waypoints, tended by `/atlas:widen` and `/atlas:deepen`.
- **`docs/`** — as-built: what the system *is*. How it works, how to operate
  it, what is reusable. Tended by `/atlas:document`.

Is and ought do not derive from each other, which is why neither folder reads
the other. The flows are one-way: design drains into specs and code through
backlog issues; docs regenerates from code. Construction's as-designed versus
as-built drawings are the prior art — both are kept, neither is a rendering of
the other, and a folder asked to serve both jobs rots at one of them.

Both corpora share the OKF substrate deliberately: one concept format, one
actor convention, one trust family, one linter (`scripts/lint_bundle.py`,
`--kind design | docs`). Two linters over one substrate would drift; the
kinds differ only where the doctrines genuinely differ — design bans `status`
and `log.md` because waypoint lifecycle lives in maps and history lives in
git; docs uses both because lifecycle and a running change log are exactly
its freshness machinery.

## The boundary with the spec corpus

`openspec/specs/` is the verification contract: what the system is *required*
to do, checked against shipped code. `docs/` is operational knowledge and the
reuse surface: what the system actually is, for the next reader who has to
work in it. Never restate a spec requirement in the bundle — point at the
owning capability spec instead. Where spec and code disagree, record the
disagreement as a finding; the spec corpus is corrected through its own
pipeline, never by documentation fiat.

`docs/` is the single source of truth for all documentation of the system —
agent-facing and user-facing. Consumers reach it through a project-local
CLAUDE.md pointer at the regenerable `docs/index.md` ("before writing a
helper, check `docs/index.md`"), the machine-owned root of progressive
disclosure. Separately maintained doc surfaces retire into the bundle
through the founding run's migration slate; rendering layers over the bundle
are licensed future work, not something a run builds.

## Ownership: the actor is the boundary

Every concept's `generated.by` actor divides the corpus into two regimes:

- **Machine-authored** concepts are a function of the code. Regeneration is
  their maintenance: when the code moves, rewrite the content and move the
  stamps with it. Nothing about their prose is precious.
- **Human-authored** concepts (`human:<id>`) are crafted prose — guides,
  tutorials, operating advice whose value is the author's voice and
  judgment. They are *not* a function of the code, so regeneration would
  destroy them — and even a one-word "correction" left under the human
  byline makes the frontmatter attest words the author never wrote: a forged
  attestation, worse than a stale claim. Your whole authority over them is
  verify-and-flag: check their claims, mark staleness in lifecycle
  frontmatter (`status: draft`, a passed `stale_after`), log the specific
  stale claim, withhold the `verified` stamp. The author retunes; you never
  ghostwrite. This rule overrides your judgment about improving text — the
  pull toward quietly fixing an obviously wrong sentence is exactly the
  failure the rule exists to stop.

This is what reconciles "docs regenerates from code" with a single source of
truth that humans also write into.

Deletion follows the same line. An orphaned concept (its subject is gone from
the code) is proposed for deletion and the operator disposes; a renamed
subject is a move, not an orphan. Machines propose; the human confirms any
removal from the corpus.

## The taxonomy

Machine concepts carry one of six code-derivable types: **Module** (a
cohesive unit of the codebase), **Helper** (the don't-reinvent reuse
surface), **CLI** (a command surface), **Playbook** (an operational
procedure), **DataModel** (on-disk and wire shapes), **API** (a served
interface). Six because each is derivable from the code by reading it — a
type an agent cannot derive has no business being machine-maintained. A
machine concept carrying any other type is stale by definition: retype it
when it is rewritten.

Helpers are documented at **group level**: one concept per cohesive group,
functions enumerated in the body. This granularity is held loosely — whether
per-function files are frontmatter noise or useful documents is an empirical
question the field record answers, not this doctrine.

Human-authored concepts carry their own types (`Guide`, and whatever a
project's authors bring next). New human types enter the doctrine by
revision when a project actually produces one — never pre-scaffolded. The
linter enforces exactly this split: the six types for machine actors,
freedom for human ones.

## Freshness is the point

`docs/` is where OKF's trust machinery earns its keep. A bundle nobody
verifies sits at the lowest trust tier forever and deserves to: a consumer
reading an unstamped concept cannot distinguish "checked yesterday" from
"wrong since March". Three mechanisms carry the whole story:

- **`generated: { by, at }`** — who wrote the current content, and when it
  last meaningfully changed. Actors follow the OKF convention:
  `<producer>/<version>` for yourself (identify your harness and model
  honestly), `human:<id>` for people.
- **`verified` events** — who confirmed the content against the source, and
  when. Machine concepts accumulate them run over run; human concepts
  receive them as the only mark a machine leaves.
- **`code_commit` pins** — the commit a concept's claims were checked
  against. The pin is what lets the next run scope itself by
  `git diff <pin>..HEAD` instead of rereading the world, and a *moved* pin
  is the only honest witness that a re-check happened — timestamps alone
  prove nothing when runs land the same day.

Indexes and `log.md` are fully regenerable machine property — appropriate
here, unlike the design bundle's stateful maps, because everything they
enumerate is recoverable from the concepts themselves. Take timestamps from
`date -u +%Y-%m-%dT%H:%M:%SZ`, never from memory.

## The run architecture

The operation is one convergent verb — make `docs/` true of the code as it
stands — carried by four phase agents, each with its own brief:

- **enumerator** — reads the bundle's stamps and the git history since its
  pins, inventories the code's subjects, and produces the concept slate:
  current / stale / new / orphaned, with the evidence for each call.
- **scribe** — one dispatch per new-or-stale machine concept; derives that
  one concept from the source and touches nothing else.
- **synthesizer** — regenerates every index and appends the run's `log.md`
  entry after the scribes land.
- **verifier** — one dispatch per concept; re-checks claims against the
  source and stamps the outcome. The only agent that ever touches a
  human-authored concept, and only in lifecycle frontmatter.

The session holding the run is a thin coordinator: it dispatches the phases,
routes verifier failures back to scribes, and holds the judgment calls that
belong to the operator — migration slate dispositions and orphan deletions —
because those are conversations, and a background agent could only relay
them. Splitting the phases across agents is also what makes the operation
scale: a bundle too large for one context converges anyway, because no agent
ever holds more than its own slice.
