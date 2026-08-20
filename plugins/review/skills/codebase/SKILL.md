---
name: codebase
description: Use when the operator asks for a full review of a settled codebase with no changes in flight — a checkup across every angle at once — production readiness, structural depth, deterministic health metrics, and docs accuracy. Coordinates the readiness, structure-miner, refactor-audit, and arcc-review agents in one parallel wave and fuses their findings into a single ranked, receipts-attached report, then routes chosen findings into draft issues. Not for PR diffs, single bugs, or work in flight.
---

# Codebase Sweep

Review a settled codebase from every angle at once and fuse the results into one findings-first report. The operator types this skill; every angle runs as a dispatched agent.

## Contract

- **Settled means settled.** Clean working tree, no work in flight. The sweep reviews a state, not a moving target.
- **All angles run.** The operator does not pick angles; a blocked angle degrades the sweep and is reported, never silently skipped.
- **Read-only.** No agent edits the target repo, and neither do you.
- **Pinned.** Every finding cites file:line against the pinned commit.

## Preflight

1. **Settled check.** `git status --porcelain` must be empty. If it isn't, stop and ask the operator: proceed anyway (findings may cite a moving target) or come back when the tree is clean.
2. **Pin the commit.** `git rev-parse HEAD`. Every agent brief carries it; the report opens with it.
3. **Gather design records.** Collect the paths that carry standing rulings: `openspec/specs/`, `DECISIONS.md`, ADR directories, the repo's `CLAUDE.md` — whatever this repo carries. A finding that walks into a standing ruling is noise; every agent brief carries these paths.
4. **Resolve docs scope.** `fd -e md -e mdx -e rst`, trim vendored and generated paths. This list goes to arcc-review so it doesn't stall mid-sweep asking for scope.

## Dispatch

One parallel wave — all seven Agent calls in a single message, every one a plain **unnamed** background dispatch (never pass `name`: each report is the dispatch's return value, and a named dispatch silently loses it):

| # | Agent | Brief carries |
|---|---|---|
| 1 | `review:readiness` | repo path, pinned commit, design-record paths |
| 2–5 | `review:structure-miner` (four dispatches) | repo path, pinned commit, design-record paths, and the lens: `pass-through`, `reappeared complexity`, `leaky interface`, or `hypothetical seam` — one per dispatch |
| 6 | `review:refactor-audit` | repo path; the agent runs its own preflight |
| 7 | `review:arcc-review` | the resolved docs scope, pinned commit |

**Degradation rule.** An angle that halts on its own preflight — refactor-audit on a repo whose language it ships no module for, or whose audit tools are not installed, is the common case — becomes a coverage note ("health angle unavailable: <reason>"), and the sweep continues. Gaps are reported, never papered over; a degraded sweep is still a sweep.

**No mid-wave questions.** Every brief tells its agent not to stall on a clarifying question: where an agent would ask, it records the gap as a coverage note and proceeds. The operator reads gaps in the report, not prompts mid-run.

## Fusion

Merge the returns in this context. Read `${CLAUDE_PLUGIN_ROOT}/references/codebase-design/FINDING-FORMAT.md` and `${CLAUDE_PLUGIN_ROOT}/references/codebase-design/VOCABULARY.md` first — miner findings arrive in that format and vocabulary, and the fusion rules below use its terms.

- **Dedup by underlying cause, not symptom.** When two angles name the same cluster — refactor-audit's churn-times-complexity hotspot and a miner's reappeared-complexity finding, say — that is one finding, promoted for convergence, with both sets of receipts attached. Say which angles agreed.
- **Adjudicate contradictions by rule, not preference.** The two-adapter test and the dependency category (`${CLAUDE_PLUGIN_ROOT}/references/codebase-design/DEEPENING.md`) decide seam disputes; readiness's authority order decides spec disputes.
- **Rank by impact × risk × leverage.** A bad metric in a file nobody touches is not a headline finding.
- **Verify before shipping.** Attack the top-ranked findings before they ship: run the deletion test against the actual callers, name the two real adapters, or cut the claim to what the evidence supports. Rank governs verification depth. Recheck the design record against each finding's final shape; survivors keep a one-line note of what was checked. Findings that fail verification are dropped or downgraded to observations — don't pad the report.

## Report

Findings first, ranked. Per finding: what is wrong, why it matters, where (evidence sites, file:line at the pinned commit), and the first mechanical step. Then:

- **Counterweight** — indirection to *remove*, from the hypothetical-seam lens. If there is none, say the sweep looked.
- **Coverage statement** — what each angle examined, what nobody examined, and which angles degraded and why. A sweep that doesn't say what it skipped implies it skipped nothing.
- **Sequencing** — dependency order across findings, which first and why.

## Routing

After the operator reviews the report, file the findings they choose as draft issues — one issue per finding, the finding format as the body, self-contained enough that a future spec session needs no re-derivation.

**Detect the forge from the git remote, then use its CLI.** Read the host once:

```bash
git remote get-url origin
```

| Remote host | CLI | Create command |
|---|---|---|
| `github.com` | `gh` | `gh issue create --title "<title>" --body-file <path>` |
| any Forgejo or Gitea host | `fj` | `fj issue create -H <host> "<title>" --body-file <path>` |
| `gitlab.com` or a self-hosted GitLab | `glab` | `glab issue create -y --title "<title>" --description-file <path>` |

glab's `-y` is load-bearing: without it, glab prompts for confirmation to submit, which blocks a non-TTY shell. Exact-match `github.com` and `gitlab.com` against the remote host. **Any other host is self-hosted, and the hostname alone cannot tell you which forge software it runs** — Forgejo, Gitea, and GitLab all live on arbitrary domains. Resolve it by evidence rather than by guessing: check which of `fj`, `glab`, and `gh` are installed, and where that is not decisive, ask the operator which forge the host runs. Confirm before filing; never file into a guess.

Then check that the CLI the table selected actually resolves — `command -v` that specific binary — before the first call. A missing binary is the fallback case below, not an error.

**When no forge CLI resolves, do not fail and do not file.** Emit each chosen finding as a ready-to-paste block — a title line and a body — and tell the operator to file them by hand. Losing the filing is a convenience cost; losing the findings is the whole review.

```markdown
### Issue 1 of N
**Title:** <one-line title>

<body: the finding format, verbatim>
```

Interface exploration for a chosen candidate uses `${CLAUDE_PLUGIN_ROOT}/references/codebase-design/DESIGN-IT-TWICE.md`.
