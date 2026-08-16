---
name: document
description: Use when a project's as-built documentation needs founding or maintenance — generating a docs/ OKF knowledge bundle from the code, bringing an existing bundle back in sync after code changes, or auditing that docs/ is still true. Triggers on requests to document what a system actually is, update stale docs, build a reuse/helper index, or "make docs match the code". One convergent operation: founding and upkeep are the same invocation.
---

# Document: make docs/ true of the code

**BACKGROUND:** `${CLAUDE_PLUGIN_ROOT}/references/document.md` carries the
doctrine behind this skill — the two-corpora model, the spec-corpus boundary,
and the rationale for the ownership and freshness rules. Read it when a
boundary call isn't settled by this file; the operational contract below is
self-sufficient for a normal run.

`docs/` is a project's as-built corpus: what the system actually is — how it
works, how to operate it, what is reusable — as an OKF knowledge bundle.
This operation is convergent: **make `docs/` true of the code as it stands.**
Run it on a repo with no bundle and it founds one; run it again after the code
moves and it converges the bundle; run it when nothing changed and it verifies
cheaply and touches almost nothing. There is no separate founding or update
mode — the state of the bundle and the git history decide what the run does.

Truth discipline: every claim derives from the code as it exists right now.
Read the source, not the README's opinion of the source. Where surfaces
disagree (README vs code, spec vs code), the bundle follows the code and
records the divergence — disagreement is a finding, not a thing to smooth over.

## Ownership: who may rewrite a concept

Every concept's `generated.by` actor decides what you may do to it. This is
the one rule in this skill that overrides your judgment about improving text.

- **Machine-authored** (`<producer>/<version>` or `process:` actors): yours.
  Rewrite freely whenever the code has made the content stale.
- **Human-authored** (`human:<id>` actors): **never edit the body, never
  reattribute — not even a one-word correction.** Crafted prose is not a
  function of the code, and an edit left under a human byline makes the
  frontmatter attest words the human never wrote. When a human concept
  contains a claim the code has falsified: leave the prose exactly as it is,
  mark the concept (`status: draft` or a passed `stale_after` date), note the
  specific stale claim in `log.md`, and surface it in your run report for the
  author to retune. Flag, don't fix.

The same boundary governs deletion: a concept whose subject vanished from the
code (not renamed — genuinely gone) is an **orphan**. Propose its deletion in
the run report and `log.md`; deleting is the operator's call. A renamed
subject is not an orphan — move the concept and update every cross-reference.

## Scope the run by git history

The run never rereads the whole world to discover nothing changed. The
enumerator reads the bundle's own stamps first, then lets git say where
drift is possible — know the mechanism so you can sanity-check its slate:

1. Find the bundle's baseline: the newest `code_commit` pin in concept
   frontmatter (or the newest `verified.at` / `generated.at` if no pins).
2. `git diff --stat <baseline>..HEAD` (excluding `docs/`) scopes the run.
   An empty diff means previously verified claims still stand — verify-stamp
   and stop. A non-empty diff names the files whose dependent concepts need
   rereading; everything else is current.
3. A concept with no `verified` event and no `code_commit` pin has never been
   checked — verify it in full regardless of history.

Every machine concept carries a `code_commit: <sha>` pin recording the
commit its claims were checked against — scribes set it when they write,
verifiers move it when they confirm. The pin is what makes step 2 possible
next time, and a moved pin is the only honest witness that a re-check
happened (same-day timestamps prove nothing).

## The run: you coordinate four phase agents

You are the thin coordinator. The work is carried by four dedicated agents —
`atlas:enumerator`, `atlas:scribe`, `atlas:synthesizer`, `atlas:verifier` —
each with its own operating contract in its agent file. You dispatch them,
route their reports, and hold the conversations that belong to the operator.
You never do a phase's work inline while its agent is available: consistent
behavior at any scale comes from every slice of work running under the same
written brief, not from whatever a single context improvises.

Trust only evidence that a dispatch took: the dispatch tool's explicit spawn
result, then the agent's report arriving. If the agent type fails to
resolve, or a dispatched agent produces no result and cannot be confirmed
running, dispatch is unavailable in your environment — do not wait on a
notification you cannot verify, and do not retry blind. Fall back: execute
the agent briefs yourself — read each file under
`${CLAUDE_PLUGIN_ROOT}/agents/` and follow it exactly, in phase order — and
say so in the report. The briefs are the direction either way; the fallback
changes who executes them, never what is done.

1. **Enumerate.** Dispatch `atlas:enumerator` with the repo root, the bundle
   directory, and a scratch path. It returns the concept slate: every
   concept classified current / stale / orphaned, new subjects typed from
   the taxonomy (`Module`, `Helper`, `CLI`, `Playbook`, `DataModel`, `API`;
   Helpers at group level — one concept per cohesive group). A machine
   concept typed outside the taxonomy is slated stale; renames ripple to
   every concept referencing the old name.
2. **Converse.** Before anything is written, put the slate's operator calls
   to the operator: orphan deletions, and on a founding run the migration
   slate. Running non-interactively, carry them as proposals in the run
   report and touch nothing they cover.
3. **Write.** Fan out `atlas:scribe` — one dispatch per new-or-stale machine
   concept, in parallel, each carrying its slate entry (why it's stale, its
   type, its source files). Scribes never touch human-authored concepts;
   nothing on the slate should send one there.
4. **Synthesize.** When the scribes land, dispatch `atlas:synthesizer` with
   the run summary. It regenerates every index and writes the dated `log.md`
   entry.
5. **Verify.** Fan out `atlas:verifier` — one dispatch per concept, every
   concept, every run: the stamps are what make the bundle trustable, so
   this phase is not optional even when nothing else changed. Route each
   failure report back to a fresh scribe dispatch and re-verify the rewrite;
   human-authored staleness flags go into the run report for the author.
   Then run the deterministic backstop yourself:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint_bundle.py" --kind docs docs/`
   must exit 0 (skip only if the script is genuinely unavailable, and say so
   in the report).

## Bundle mechanics (OKF v0.2, the load-bearing subset)

- Every concept: YAML frontmatter with a non-empty `type`, plus `title`,
  `description`, `tags`, `status` where useful. Root `index.md` may carry
  only `okf_version: "0.2"`; other indexes and `log.md` carry no frontmatter.
- Provenance: `sources` entries whose `resource` paths point at the real
  files the concept derives from; they must resolve. `generated: { by, at }`
  uses the actor convention — `<producer>/<version>` for yourself,
  `human:<id>` for people. Your actor string identifies your harness and
  model honestly.
- Freshness: `verified` events accumulate as a list; `stale_after` is an
  absolute date, set when content has a known decay horizon; `status:
  draft | stable | deprecated`.
- Links between concepts are ordinary markdown links; keep them resolving
  after moves and renames.

## Founding extras

Only on a run that creates the bundle:

- **Migration slate.** Inventory the repo's existing doc surfaces (README,
  doc folders, wikis, per-project reuse indexes) and propose a disposition
  for each: **absorb** (content regenerates into concepts, old surface
  retires), **retire** (obsolete), or **leave alone** (still owns its job —
  README quickstarts, spec surfaces). The operator disposes; running
  non-interactively, put the slate in the run report and touch none of them.
- **The pointer.** Consumers find the bundle through a project-local
  CLAUDE.md line pointing at `docs/index.md` ("before writing a helper,
  check `docs/index.md`"). Add it unless constrained to touch only `docs/`;
  then propose it in the report.

## The run report

End every run by reporting: what drifted and how you knew, what you rewrote,
created, moved; what you verified clean and deliberately left untouched;
every flag on human-authored content (the claim, the file, why it's stale);
orphan-deletion and migration-slate proposals awaiting the operator; and
divergences recorded but out of scope (README, specs). The report is the
operator's half of the conversation — anything requiring their judgment
lives there, not in silent edits.
