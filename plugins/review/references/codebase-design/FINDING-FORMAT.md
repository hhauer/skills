# Finding format

Every finding, from every miner, carries:

1. **Candidate** — the module or cluster, named.
2. **Lens and principle** — which lens caught it, which principle it fails, stated in the codebase-design vocabulary.
3. **Evidence sites** — file:line, enumerated. For reappeared complexity: every copy. For leaky interfaces: the callers doing the compensating. "Used in many places" is not evidence.
4. **Design-record check** — no standing ruling touches this, or names the ruling and how the finding is scoped around it (or proposes reopening it, with the new evidence).
5. **Dependency category and testing strategy** — classify per DEEPENING.md and state how the deepened module would be tested: real dependency, local stand-in, injected fake at a port, or mock. "Easier to test" without the category is unfinished.
6. **Leverage estimate** — what callers and maintainers gain; where the payback is thin, say so.
7. **First step** — the smallest mechanical move that starts the refactor (often a test that pins current behaviour).

Findings in this format are comparable and mergeable without re-derivation: the miner writes it, and the sweep coordinator's fusion step reads it. Terms are pinned by VOCABULARY.md.
