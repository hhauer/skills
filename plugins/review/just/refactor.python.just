# ABOUTME: Python refactor-audit recipes, bundled with the review plugin and
# ABOUTME: mounted by python.just, which review:refactor-audit points --justfile
# ABOUTME: at to run `refactor::<recipe>` from the target repo root.

import 'refactor.common.just'

tpl := justfile_directory() + "/templates"

# Every recipe in this family runs against the project that invoked just,
# not against the directory where this module file lives. `[no-cd]` keeps
# just from chdir'ing into the directory this module lives in before running.

# uv discipline, uniform across the module: an audit never rewrites uv.lock.
# `preflight` is the one recipe allowed to sync the environment — proving the
# pinned tools are runnable is its whole job — so it runs `uv run --locked`,
# which turns a drifted lock into an error instead of a silent rewrite. Every
# analysis recipe after it runs `uv run --no-sync`, which touches neither the
# lock nor the venv. The two flags are never combined: with --no-sync there is
# no lock operation left for --locked to assert, so the check goes quiet.
# `uv add` in the operator-invoked `install` is the sole exception — relocking
# is the point there.

# The trailing import-linter check is the one non-halting step: `lint-imports --help`
# exits 0 whether or not contracts are configured, so an unconfigured project would
# look ready here and fail at architecture. It warns and exits 0 rather than halting,
# because a preflight failure stops the whole audit — worse than the one red step it
# would be reporting.
# Verify global + project-pinned tools are runnable; halt-on-failure.
[no-cd]
preflight:
    @echo "=== refactor::preflight (python) ==="
    @echo "--- Global ---"
    @scc --version
    @jscpd --version
    @lizard --version
    @semgrep --version
    @gitleaks version
    @osv-scanner --version
    @git --version
    @echo ""
    @echo "--- Project (via uv run) ---"
    @uv run --locked ruff --version
    @uv run --locked ty --version
    @uv run --locked vulture --version
    @uv run --locked bandit --version
    @uv run --locked pip-audit --version
    @uv run --locked pydeps --version > /dev/null
    @uv run --locked lint-imports --help > /dev/null
    @uv run --locked python -c "import pytest_cov; print('pytest-cov', pytest_cov.__version__)"
    @if [ -e .importlinter ] || grep -q '^\[importlinter\]' setup.cfg 2>/dev/null || grep -q '^\[tool\.importlinter\]' pyproject.toml 2>/dev/null; then :; else echo '!! no import-linter config found (.importlinter / setup.cfg / pyproject.toml) — refactor::architecture will fail; run: just --justfile "${CLAUDE_PLUGIN_ROOT}/just/python.just" refactor::install'; fi

# Contract conformance — does the code match the intended architecture?
[no-cd]
architecture:
    @echo "=== refactor::architecture (python) ==="
    @uv run --no-sync lint-imports

# pydeps takes the package *directory*; we resolve it from pyproject's
# [project].name (- normalized to _), trying the src-layout path then the flat
# layout. That match is a project convention, so the resolution is
# a contract rather than a guess — a miss means the project broke the convention,
# and the error says so instead of hunting for a package to fall back on. --no-output skips SVG render (no graphviz needed). --show-cycles exits
# after printing, so it's a separate invocation from --show-deps. This is the
# graph-emitter half; architecture (above) is the import-linter contract check —
# the same split Go and TS use.
# Dependency graph shape: import cycles, then the module dependency dict.
[no-cd]
deps:
    @echo "=== refactor::deps (python) ==="
    @name=$(uv run --no-sync python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['name'].replace('-','_'))"); \
      if [ -d "src/$name" ]; then pkg="src/$name"; elif [ -d "$name" ]; then pkg="$name"; else echo "refactor::deps: cannot locate package dir for '$name' (tried src/$name and $name) — [project].name must match the package directory" >&2; exit 1; fi; \
      echo "--- pydeps: import cycles ($pkg) ---"; \
      uv run --no-sync pydeps "$pkg" --no-output --show-cycles; \
      echo ""; \
      echo "--- pydeps: dependency dict ($pkg) ---"; \
      uv run --no-sync pydeps "$pkg" --no-output --show-deps

# Lizard is polyglot and host-global — same tool as the TS module. Output is a
# per-function CCN + NLOC + parameter count + nesting table, plus per-file
# averages and a warnings block for hotspots. || true so the warnings exit
# (lizard returns 1 when CCN > 15 threshold is hit) doesn't halt downstream
# recipe lines.
# Per-function complexity table via lizard.
[no-cd]
complexity:
    @echo "=== refactor::complexity (python) ==="
    @lizard -s cyclomatic_complexity -x '*test*' . || true

# Dead code — functions, classes, vars with no caller.
[no-cd]
dead-code:
    @echo "=== refactor::dead-code (python) ==="
    @uv run --no-sync vulture --exclude=.venv,.tox,build,dist,__pycache__ --min-confidence 80 .

# Lint-debt density per file.
[no-cd]
lint-debt:
    @echo "=== refactor::lint-debt (python) ==="
    @uv run --no-sync ruff check --statistics .

# Type coverage and strictness gaps.
[no-cd]
types:
    @echo "=== refactor::types (python) ==="
    @uv run --no-sync ty check

# osv-scanner (OSV.dev) complements pip-audit (PyPI advisory) — different
# advisory sources, each catches things the other misses.
# Known-vuln deps + bandit security smell.
[no-cd]
security:
    @echo "=== refactor::security (python) ==="
    @echo "--- bandit (low-severity and up) ---"
    @uv run --no-sync bandit -r . -ll --exclude './.venv,./.tox,./build,./dist' || true
    @echo ""
    @echo "--- pip-audit ---"
    @uv run --no-sync pip-audit || true
    @echo ""
    @echo "--- osv-scanner (OSV.dev, auto-detects uv.lock / requirements.txt) ---"
    @osv-scanner scan source . || true

# Test suite + coverage; broken tests are themselves a finding.
[no-cd]
tests:
    @echo "=== refactor::tests (python) ==="
    @uv run --no-sync pytest --cov --cov-report=term-missing

# Drops a default .importlinter if the project has no import-linter config yet — never
# clobbers tuned contracts (the architecture recipe cannot run at all without a config;
# the default's acyclic_siblings contract is the Python analog of the no-circular rule
# the TS module's dependency-cruiser default provides). acyclic_siblings needs
# import-linter >=2.6; uv add is deliberately left unversioned so it installs latest on
# a fresh project and never rewrites a project's existing pin — a project pinned below
# 2.6 gets an unknown-contract-type error from lint-imports, which names the problem.
# root_package must name a real package, so it's resolved
# from pyproject's [project].name the same way `deps` resolves the package dir; when
# that fails the config is skipped with a message rather than aborting, because uv add
# has already run by then and a half-finished install is worse than a missing config —
# preflight warns about the gap on every subsequent run.
# Install the audit's dev-tool requirements and default configs (operator-invoked).
[no-cd]
install:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "=== refactor::install (python) ==="
    uv add --group dev vulture bandit pip-audit import-linter pytest-cov pydeps
    name=$(uv run --no-sync python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['name'].replace('-','_'))" 2>/dev/null || true)
    if [ -e .importlinter ] || grep -q '^\[importlinter\]' setup.cfg 2>/dev/null || grep -q '^\[tool\.importlinter\]' pyproject.toml 2>/dev/null; then
      echo "import-linter config already present — leaving it untouched"
    elif [ -z "$name" ]; then
      echo "no .importlinter written: could not read [project].name from pyproject.toml — write one by hand (see {{ tpl }}/importlinter.ini)"
    elif [ ! -d "src/$name" ] && [ ! -d "$name" ]; then
      echo "no .importlinter written: cannot locate package dir for '$name' (tried src/$name and $name) — [project].name must match the package directory, or write one by hand (see {{ tpl }}/importlinter.ini)"
    else
      sed "s/__ROOT_PACKAGE__/$name/g" "{{ tpl }}/importlinter.ini" > .importlinter
      echo "dropped default .importlinter (forbids sibling cycles; tune as needed)"
    fi
    if [ -e .jscpd.json ]; then
      echo ".jscpd.json present — leaving it untouched"
    else
      cp "{{ tpl }}/jscpd.json" .jscpd.json
      echo "dropped default .jscpd.json (baseline duplication ignores; extend per project)"
    fi
