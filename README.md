# skills

Three Claude Code plugins, built for my own daily work and published as a marketplace.

- `atlas` maintains two kinds of version-controlled knowledge bundles: a map of a project's open design questions under `design/`, and as-built documentation under `docs/`.
- `review` audits a settled codebase and the docs that describe it.
- `forgejo` documents the `fj` CLI for agents working against Forgejo and Gitea remotes.

Where a plugin adapts prior art, its `NOTICE.md` records what was borrowed and under which license.

## Install

Add the marketplace, then install what you want:

```
/plugin marketplace add hhauer/skills
/plugin install atlas@hhauer-skills
/plugin install review@hhauer-skills
/plugin install forgejo@hhauer-skills
```

Each plugin stands alone. Installing one does not require the others.

## atlas — design maps and as-built docs

Both bundle kinds conform to the [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog) and live in the repo, so design intent and documentation are versioned alongside the code they describe.

Three skills, each invoked as a slash command:

- `/atlas:widen` fans out over one region of a problem and maps its open questions as *waypoints*, with named fog for what is not yet sharp enough to phrase as a question. It records questions without answering them; resolution belongs to deepen. Research and prototype waypoints are handed to background agents, so they never block the session.
- `/atlas:deepen` resolves one waypoint at a time in conversation. A decision enters the record only with the reason it was made and a human verification stamp; the agent cannot resolve a waypoint on its own. Findings that landed from background agents are swept onto the maps first, and when a subtree has no open questions left, the session offers to slice its resolved design into issue-sized units. Filing those is left to whatever backlog tool the project uses; the bundle records their build order.
- `/atlas:document` generates and maintains a `docs/` bundle derived from the code. Founding a bundle and updating one are the same invocation: the run reads each concept's recorded commit pin, asks git what changed since, rewrites the concepts that went stale, regenerates the indexes, and re-verifies every concept against source. Prose a human wrote is flagged when the code contradicts it, never rewritten.

`scripts/lint_bundle.py` enforces the mechanical invariants of both bundle kinds: frontmatter conformance, the human-verified decision rule, map-state integrity, and provenance that resolves. Each skill runs it before committing. It is stdlib-only Python 3 and ships with its own test suite.

atlas ends at the bundle. It assumes no issue tracker, no CI system, and no particular way of turning a resolved design into code.

## review — codebase and documentation review

`/review:codebase` reviews a settled repo (clean tree, no work in flight) through four agents dispatched in one parallel wave, then fuses the returns into a single ranked report with raw tool output attached as evidence:

- `readiness` checks whether the system is deployable and wired at runtime, judged against whatever governing spec surface the repo carries (a spec tree, an ADR directory, `DECISIONS.md`), with the README last in authority. A repo with no spec surface gets that reported as a finding.
- `structure-miner` sweeps the repo once per structural lens (pass-through, reappeared complexity, leaky interface, hypothetical seam), citing evidence sites at a pinned commit.
- `refactor-audit` runs a fixed sequence of deterministic tools: complexity, architecture contracts, dependency shape, duplication, dead code, lint debt, types, security, history, coverage. The `just` recipe library it drives ships inside the plugin, so the target project needs no justfile of its own. The tools themselves must already be installed; a missing one halts the audit with a report rather than being worked around. Supported languages: Python, TypeScript, Go.
- `arcc-review` checks documentation for accuracy, relevancy, clarity, and consistency, verifying each claim against the repo rather than taking the doc's word for it.

An angle that cannot run becomes a coverage note, and the report states what nobody examined. Findings the operator selects are filed as draft issues through whichever forge CLI the git remote resolves to (`gh`, `fj`, `glab`), or printed for hand-filing when none is installed.

Two more entry points work on their own:

- `/review:survey` brings a repo's README, its `CLAUDE.md` files, and the agent's stored memories about the project back in line with the current state of the repo.
- `review:design-adversary` is a standalone agent that gives a design doc, spec, or plan an adversarial reading, pins every finding to quoted text, names what would refute it, and reports what held as well as what did not.

## forgejo — the `fj` skill

`fj` is the CLI for Forgejo and Gitea instances. It resembles `gh` closely enough that most habits transfer, and this skill documents the differences that matter to an agent, verified against `fj v0.6.0`: repo-targeting flags that behave differently from `gh -R`, `search` in place of the `list` verb, label creation that silently duplicates instead of failing, bare flags that open `$EDITOR` and hang a non-interactive session, and the invisible Unicode directional isolates in `fj` output that break naive parsers. Nothing in it is tied to a particular instance; `-H <host>` covers the cases where `fj` cannot resolve the host from the remote. Requires the `fj` CLI on the PATH.

## Development

Each skill was written against a measured baseline: run the task without the skill, keep the transcript, then iterate the skill until subagent A/B runs beat that baseline, and pressure-test its judgment rules by giving a fresh agent a plausible reason to work around them. [Anthropic's skill-creator](https://github.com/anthropics/claude-plugins-official) supplies the eval harness; [Superpowers](https://github.com/obra/superpowers) supplies the pressure-testing method.

## Scope

- No project scaffolding or environment setup. Those plugins depend on my own dotfiles and machine layout, so they are not published.
- No language servers. Anthropic's official marketplace has good ones.
- The design records, evaluation workspaces, and issue history live in a private repo; these plugins are the shipped artifact.

## License

MIT, see `LICENSE`. Vendored reference material under a plugin's `references/` keeps its own license: `review` bundles the Diátaxis framework (CC-BY-SA 4.0) and one MIT document, and `atlas` adapts MIT-licensed prior art and an Apache-2.0 format specification. Details in each plugin's `NOTICE.md`.
