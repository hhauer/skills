# CLAUDE.md

## This is a delivery repo

This repo exists to be installed. It holds Claude Code plugins — one
directory each under `plugins/` — as a marketplace.

**These plugins are authored from a separate private workbench**, normally
this checkout's parent directory. That workbench carries the
skill-design rules, the eval-driven authoring method, the prose
anti-pattern reference, and the backlog. **If it is available, read its
`CLAUDE.md` before editing anything here.** Issues on this repo are
disabled; planning happens in the workbench.

If you are working in this repo on its own, the plugins are self-contained
and the rules below are the ones that matter.

## The rule that lives here

**Every change to a plugin requires bumping `version` in
`plugins/<name>/.claude-plugin/plugin.json`.** Consumers pull updates by
version, so a content edit shipped with an unchanged version never reaches
an installed copy. Bias toward minor and patch; major is for removing or
renaming a skill or agent, or changing an invocation contract. When the
bump changes what a plugin *contains*, sync its description in
`.claude-plugin/marketplace.json` too — that is a second copy of the same
fact and drifts silently.

## Conventions

- **Cross-references are plugin-namespaced**: `review:arcc-review`,
  `forgejo:fj`. Bare names break once content ships as a plugin.
- **Paths into bundled files use `${CLAUDE_PLUGIN_ROOT}`**, never
  repo-relative paths — at runtime the plugin is installed elsewhere.
- **Vendored reference material keeps its own license.** Where a plugin
  carries any, its `NOTICE.md` says so.

## The executable code

- `plugins/atlas/scripts/lint_bundle.py` validates an OKF v0.2 knowledge
  bundle. Tests: `python3 plugins/atlas/scripts/test_lint_bundle.py`.
- `plugins/review/just/` holds the recipe library `review:refactor-audit`
  runs: one `refactor.<lang>.just` module per language importing the shared
  `refactor.common.just`, a one-line `<lang>.just` mount file per language,
  and `templates/` config seeds the recipes copy into projects. After
  editing a `.just` file:
  `just --fmt --check --justfile plugins/review/just/<file>`.

## Version control

Work on a branch; landing on main needs the maintainer's explicit approval.
