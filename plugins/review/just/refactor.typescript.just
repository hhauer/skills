# ABOUTME: TypeScript refactor-audit recipes, bundled with the review plugin and
# ABOUTME: mounted by typescript.just, which review:refactor-audit points --justfile
# ABOUTME: at to run `refactor::<recipe>` from the target repo root.

import 'refactor.common.just'

tpl := justfile_directory() + "/templates"

# Every recipe in this family runs against the project that invoked just,
# not against the directory where this module file lives. `[no-cd]` keeps
# just from chdir'ing into the directory this module lives in before running.

# Lint doctrine: oxlint is the linter. Svelte projects additionally
# carry eslint + eslint-plugin-svelte scoped to .svelte files — oxlint lints
# only script blocks in framework files, so template linting needs eslint there.
# An eslint flat config (eslint.config.*) is the marker for that hybrid; the
# eslint checks in this module run only when one is present.
# Verify global + project-pinned tools are runnable; halt-on-failure.
[no-cd]
preflight:
    @echo "=== refactor::preflight (typescript) ==="
    @echo "--- Global ---"
    @scc --version
    @jscpd --version
    @semgrep --version
    @gitleaks version
    @lizard --version
    @osv-scanner --version
    @git --version
    @echo ""
    @echo "--- Project (via pnpm exec) ---"
    @pnpm exec oxlint --version
    @if ls eslint.config.* >/dev/null 2>&1; then pnpm exec eslint --version; fi
    @pnpm exec depcruise --version
    @pnpm exec knip --version
    @pnpm exec type-coverage --version

# err-long (not text) because only the err/err-long reporters propagate
# depcruise's non-zero exit code on an error-severity violation — the text
# reporter always exits 0, silently masking a red contract. err-long also
# prints each violation with its rule comment.
# Contract conformance via dependency-cruiser.
[no-cd]
architecture:
    @echo "=== refactor::architecture (typescript) ==="
    @pnpm exec depcruise --validate --output-type err-long src

# depcruise's --validate path covers cycle detection when the project's
# .dependency-cruiser.cjs declares a no-circular rule; that's the canonical
# place for it, not a duplicate tool.
# Dependency graph: structural summary via depcruise.
[no-cd]
deps:
    @echo "=== refactor::deps (typescript) ==="
    @pnpm exec depcruise --output-type text src

# Lizard is polyglot and sortable, giving CCN + NLOC + parameter count +
# nesting depth per function (not just a single pass/fail threshold the way
# an eslint complexity rule does).
# Per-function complexity table via lizard.
[no-cd]
complexity:
    @echo "=== refactor::complexity (typescript) ==="
    @lizard -s cyclomatic_complexity -x '*test*' -x 'node_modules/*' -x 'build/*' -x '.svelte-kit/*' .

# Dead files, exports, and unused dependencies.
[no-cd]
dead-code:
    @echo "=== refactor::dead-code (typescript) ==="
    @pnpm exec knip --reporter compact

# The eslint pass joins in only on Svelte-hybrid projects (flat config
# present), where it covers the .svelte files its config scopes.
# Lint-debt density: oxlint always, plus eslint on Svelte-hybrid projects.
[no-cd]
lint-debt:
    @echo "=== refactor::lint-debt (typescript) ==="
    @pnpm exec oxlint
    @if ls eslint.config.* >/dev/null 2>&1; then pnpm exec eslint --report-unused-disable-directives .; fi

# --ignore-files excludes match the complexity recipe's lizard -x set:
# adapter/SvelteKit/generic build outputs that would otherwise pollute
# the percentage with minified vendor code.
# Type coverage — where is the code escaping the type system?
[no-cd]
types:
    @echo "=== refactor::types (typescript) ==="
    @pnpm exec type-coverage --detail --ignore-files 'build/**' --ignore-files '.svelte-kit/**' --ignore-files 'node_modules/**' --ignore-files 'dist/**'

# osv-scanner (OSV.dev, broad ecosystem coverage) and pnpm audit (npm
# advisory db) are complementary — each catches things the other misses.
# Known-vuln deps via osv-scanner and pnpm audit.
[no-cd]
security:
    @echo "=== refactor::security (typescript) ==="
    @echo "--- osv-scanner (OSV.dev, auto-detects pnpm-lock.yaml / package-lock.json) ---"
    @osv-scanner scan source . || true
    @echo ""
    @echo "--- pnpm audit (npm advisory db) ---"
    @pnpm audit --audit-level=moderate || true

# --coverage uses vitest's default v8 provider; install adds
# @vitest/coverage-v8 to the project for that.
# Test suite + coverage.
[no-cd]
tests:
    @echo "=== refactor::tests (typescript) ==="
    @pnpm exec vitest run --coverage

# Drops a default .dependency-cruiser.cjs if the project has no dependency-cruiser
# config yet — never clobbers a tuned config (the architecture/deps recipes need a
# config with a no-circular rule, which the default's `extends recommended`
# provides). oxlint is assumed to already be a project dep;
# Svelte-hybrid projects own their eslint + eslint-plugin-svelte stack themselves,
# so this install adds no lint tooling.
# Install the audit's project-level dev-tool requirements and default configs (operator-invoked).
[no-cd]
install:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "=== refactor::install (typescript) ==="
    pnpm add --save-dev --save-exact dependency-cruiser knip type-coverage @vitest/coverage-v8
    if [ -e .dependency-cruiser.cjs ] || [ -e .dependency-cruiser.js ] || [ -e .dependency-cruiser.mjs ] || [ -e .dependency-cruiser.json ]; then
      echo "dependency-cruiser config already present — leaving it untouched"
    else
      cp "{{ tpl }}/dependency-cruiser.cjs" .dependency-cruiser.cjs
      echo "dropped default .dependency-cruiser.cjs (extends recommended; tune as needed)"
    fi
    if [ -e .jscpd.json ]; then
      echo ".jscpd.json present — leaving it untouched"
    else
      cp "{{ tpl }}/jscpd.json" .jscpd.json
      echo "dropped default .jscpd.json (baseline duplication ignores; extend per project)"
    fi
