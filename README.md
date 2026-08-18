# skills

Three Claude Code plugins I built for my own work and use daily.

- `atlas` maps a project's open design questions before they are answered, and keeps as-built documentation true of the code.
- `review` audits a settled codebase and the docs that describe it.
- `forgejo` carries what an agent needs to drive Forgejo and Gitea repositories from the command line.

They are original plugins rather than a curated list of other people's. Where one adapts prior art, that plugin's `NOTICE.md` records what was borrowed and under which license: `atlas` adapts Matt Pocock's `wayfinder` skill and conforms to the Open Knowledge Format v0.2, and `review` bundles the Diátaxis documentation framework and material mined from the same skills collection.

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

Atlas covers two problems on one substrate. Some work is too large and too undecided to plan in a single session, and the reasoning behind what you eventually build evaporates into chat logs. Separately, documentation drifts from the code the moment it is written, because nothing forces it to update.

`atlas` keeps both in version-controlled knowledge bundles conforming to the [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog).

`/atlas:widen` fans out breadth-first over one region of a problem and produces a map of the open questions — *waypoints* — plus named fog for what is not yet sharp enough to phrase as a question. It answers nothing on purpose, including the questions it could answer immediately. Research and prototype waypoints are handed to background agents so they never block the session.

`/atlas:deepen` takes one waypoint at a time and resolves it in conversation. A decision is recorded only with the reason it was made and a human verification stamp, so the agent cannot quietly resolve a waypoint on your behalf. Findings that landed from background agents get swept onto the maps first, and when a subtree goes quiet the session offers to slice its resolved design into issue-sized units. Filing them is left to whatever backlog tool the project uses; the bundle owns the slice and the map slot that records their build order.

`/atlas:document` generates and maintains a `docs/` bundle derived from the code itself. Founding a bundle and updating one are the same invocation: the run reads each concept's recorded commit pin, asks git what has changed since, rewrites the concepts that went stale, regenerates the indexes, and re-checks every concept against source. Prose a human wrote is flagged when the code falsifies it, never rewritten under that human's byline.

`scripts/lint_bundle.py` enforces the mechanical invariants of both bundle kinds — frontmatter conformance, the human-verified decision rule, map-state integrity, provenance that resolves — and each skill runs it before committing. It is stdlib-only Python and ships with its own test suite.

Atlas's deliverable is the bundle. It assumes no issue tracker, no CI system, and no particular way of turning a resolved design into code.

## review — codebase and documentation review

Review tooling tends to produce either a wall of low-signal lint output or a confident narrative with nothing behind it. `/review:codebase` runs a settled repo through four angles in one parallel wave and fuses the returns into a single ranked report with the raw tool output attached as receipts.

- `readiness` asks whether the system is deployable and wired at runtime rather than merely component-complete, judged against whatever governing spec surface the repo carries: a spec tree first, scaffold and architecture-decision docs second, the README last. A repo with no spec surface gets told so as a finding.
- `structure-miner` works four structural lenses (pass-through, reappeared complexity, leaky interface, hypothetical seam), one dispatch per lens, each sweeping the whole repo and citing evidence sites against a pinned commit.
- `refactor-audit` walks a fixed sequence over deterministic tools: complexity, architecture contracts, dependency shape, duplication, dead code, lint debt, security, history, coverage. It reasons over the raw output instead of summarizing it. The `just` recipe library it drives ships inside the plugin, so a project needs no justfile of its own; the tools themselves must already be installed, and a missing one halts the audit loudly rather than being silently worked around. Python, TypeScript, and Go have modules.
- `arcc-review` checks the docs for accuracy, relevancy, clarity, and consistency, verifying every claim against the live repo rather than against what the doc sounds like it should say.

An angle that cannot run becomes a coverage note and the sweep continues, and the report states what nobody examined. Findings carry severity, evidence sites at the pinned commit, and the first mechanical step. Ones you pick are filed as draft issues through whichever forge CLI the git remote resolves to (`gh`, `fj`, `glab`), and printed for hand-filing when none is installed.

Two more entry points work on their own. `/review:survey` brings a repo's README, its `CLAUDE.md` files, and the agent's stored memories about the project back in line with what the repo has become. `review:design-adversary` gives a design doc, spec, or plan the least charitable competent reading it can, pinning every finding to quoted text and naming what would refute it, and reporting what held as well as what did not.

## forgejo — the `fj` skill

`fj` is the CLI for Forgejo and Gitea instances, shaped closely enough like `gh` that most instincts transfer and the ones that do not cost an agent a failed round trip each. The skill is that delta, verified against `fj v0.6.0`: repo-targeting flags where `-R` does not mean what `gh` means by it, `search` in place of the `list` verb, label creation that silently makes a duplicate instead of failing, the bare flags that open `$EDITOR` and hang a non-interactive agent, and the invisible Unicode directional isolates wrapped around every field of `fj` output that break naive parsers. Nothing in it is tied to a particular instance; `-H <host>` covers the cases where `fj` cannot resolve the host from the remote.

## How these were built

Skills are prompts, and prompts are testable. Each of these was built the same way:

1. Run the task **without** the skill and keep the transcript. That is the baseline, and it is usually better than expected, which is the point.
2. Write the smallest skill that beats the baseline on the specific thing the baseline got wrong.
3. Measure against the baseline with subagent A/B runs, then iterate.
4. Pressure-test the judgment calls: give a fresh agent a plausible reason to rationalize its way around a rule and see whether the rule holds.

The discipline this enforces is subtraction. A skill that does not beat its baseline does not ship, and most of the editing after the first draft removes instructions that turned out to carry no weight. [Anthropic's skill-creator](https://github.com/anthropics/claude-plugins-official) supplies the eval harness; [Superpowers](https://github.com/obra/superpowers) supplies the method for pressure-testing judgment skills.

## Scope

What is here is what I use. What is not here:

- No project scaffolding or environment setup. Those plugins are welded to my own dotfiles and machine layout and would not work for you.
- No language servers. Anthropic's official marketplace has good ones.
- The design records, evaluation workspaces, and issue history live in a private repo. These plugins are the artifact; the reasoning behind each decision is not published.
- `atlas` ends at the bundle. Turning a resolved design into tracked work, specs, or code is deliberately not part of it.

## License

MIT, see `LICENSE`. Vendored reference material under a plugin's `references/` keeps its own license; see that plugin's `NOTICE.md`. `review` bundles the Diátaxis framework under CC-BY-SA 4.0 and one document under MIT, and `atlas` adapts MIT-licensed prior art and an Apache-2.0 format specification.
