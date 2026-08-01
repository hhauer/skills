---
name: deepening-audit
description: Use when mining a mature, organically grown codebase for structural refactoring candidates — shallow modules, duplicated pipelines, leaky interfaces, unearned abstraction — to find where refactoring would deepen modules and improve reusability. For code that has lived long enough to prove it works, not for greenfield design or a single PR review.
---

# Deepening Audit

Mine a mature codebase for **deepening candidates**: places where restructuring modules and their interfaces would concentrate behaviour behind smaller surfaces. Produce verified, deduplicated findings routable into the project's backlog.

**REQUIRED SUB-SKILL:** the audit's shared language is `review:codebase-design`. Read `${CLAUDE_PLUGIN_ROOT}/skills/codebase-design/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/skills/codebase-design/references/DEEPENING.md` before doing anything else; every miner brief and every finding uses that vocabulary.

## When to use

- The operator asks for a refactor-mining pass, a depth/structure audit, or "where would restructuring pay off" on a codebase with real history.
- Not for greenfield or in-flight design: the deletion test and the two-adapter rule are empirical — they need existing callers. A codebase without callers has nothing to measure.
- Not for a PR diff or a single named bug.
- Distinct from `review:refactor-audit` (deterministic-tool-driven: complexity × churn × duplication metrics) — this audit is judgment-driven and the two deliberately stay separate; where both converge on the same code, say so, it's evidence.

## Ground rules

1. **Read the design record before mining.** Rulings and decision logs (`DECISIONS.md`, `openspec/specs/`, ADRs, CLAUDE.md — whatever the repo carries) are ground truth for what has already been decided. A finding that walks into a standing ruling is noise, not insight. Scope findings around rulings; where new evidence genuinely challenges one, say explicitly that the finding proposes reopening it, and with what. Pass the design-record paths to every miner.
2. **Read-only.** The audit never edits the target repo.
3. **Pin the tree.** Record the commit the audit ran against; findings cite file:line against that commit.
4. **Deterministic tools seed, they don't decide.** Complexity (`lizard`), fan-in/fan-out, and churn/co-change point at hot clusters. Token-based duplication tools (`jscpd`) systematically miss structural duplication — five hand-copied pipelines can score under 1% because identifiers differ. Treat near-zero duplication scores as "the tool can't see it," never as "there is none."

## The mining pass

Partition by **lens, not by code region**. Deepening signals are cross-regional: the deletion test's "complexity reappears across N callers" is invisible to any region shard that doesn't contain all N sites. Each miner sweeps the whole repo for one narrow signature.

Dispatch four miners in parallel (Agent tool), each briefed with: the repo path and pinned commit, the design-record paths, the two codebase-design skill files to read first, its lens below, and the finding format. Read-only, whole-repo scope, evidence enumerated.

- **Pass-through** — modules whose interface is nearly as large as their implementation; wrappers the deletion test would erase without complexity reappearing anywhere.
- **Reappeared complexity** — the same structure implemented N times because a deep module was never built: parallel pipelines, mirrored construction sites, copy-derived siblings. Structural resemblance counts; textual identity is not required.
- **Leaky interface** — callers that must know internals to call correctly: ordering constraints, config threaded hand-to-hand, compensating patches in consumers, tests reaching past the interface, private symbols imported across modules.
- **Hypothetical seam** — the counterweight: single-adapter ports, indirection nothing varies across, abstraction nobody consumes. This lens keeps the report from reading "add more abstraction everywhere."

## Finding format

Every finding, from every miner, carries:

1. **Candidate** — the module or cluster, named.
2. **Lens and principle** — which lens caught it, which principle it fails, stated in the codebase-design vocabulary.
3. **Evidence sites** — file:line, enumerated. For reappeared complexity: every copy. For leaky interfaces: the callers doing the compensating. "Used in many places" is not evidence.
4. **Design-record check** — no standing ruling touches this, or names the ruling and how the finding is scoped around it (or proposes reopening it, with the new evidence).
5. **Dependency category and testing strategy** — classify per DEEPENING.md and state how the deepened module would be tested: real dependency, local stand-in, injected fake at a port, or mock. "Easier to test" without the category is unfinished.
6. **Leverage estimate** — what callers and maintainers gain; where the payback is thin, say so.
7. **First step** — the smallest mechanical move that starts the refactor (often a test that pins current behaviour).

## Synthesis

Merge the four miners' reports yourself — this is why the vocabulary is pinned; findings arrive comparable.

- **Dedup by seam, not by symptom.** Two lenses describing the same underlying missing module are one finding. Convergence is evidence: promote it and say which lenses agreed.
- **Adjudicate contradictions by rule, not preference.** When one analysis wants a seam and another calls it unearned, the two-adapter rule and the dependency category decide. A category-2 dependency (local stand-in exists) does not get a port for testability — the stand-in already is the second adapter, inside the tests.
- Rank by leverage. Sequence findings that depend on each other and say which order and why.

## Verification

Before a finding ships, attack it:

- Run the deletion test against the actual callers — does complexity really reappear, at the cited sites?
- For any proposed seam: what are the two real adapters? Name them or cut the proposal to what the evidence supports.
- Check the design record one more time against the final shape of the finding.

Findings that survive keep a one-line note of what was checked. Findings that don't are dropped or downgraded to observations — don't pad the report.

## Report

Findings first, ranked, in the finding format. Rank governs length: the findings that head the ranking get the full format; low-leverage findings and downgraded observations compress to a few lines each — candidate, verdict, first step. Then:

- **Counterweight section** — indirection to *remove*, from the hypothetical-seam lens. If there is none, say the audit looked.
- **Coverage statement** — which clusters each lens actually examined, and what nobody examined. An audit that doesn't say what it skipped implies it skipped nothing.
- **Suggested sequencing** — dependency order across findings.

## Routing

After the operator reviews the report, file the candidates they want tracked as draft issues in the project's tracker (for Forgejo repos, `dev-tools:fj`) — one issue per finding, self-contained enough that a future propose session needs no re-derivation: the finding format is the issue body. Deepening changes then flow through the project's normal spec/implementation pipeline; a chosen candidate's interface exploration uses `${CLAUDE_PLUGIN_ROOT}/skills/codebase-design/references/DESIGN-IT-TWICE.md`.
