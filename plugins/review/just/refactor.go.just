# ABOUTME: Go refactor-audit recipes, bundled with the review plugin and
# ABOUTME: mounted by go.just, which review:refactor-audit points --justfile
# ABOUTME: at to run `refactor::<recipe>` from the target repo root.

import 'refactor.common.just'

tpl := justfile_directory() + "/templates"

# Every recipe in this family runs against the project that invoked just,
# not against the directory where this module file lives. `[no-cd]` keeps
# just from chdir'ing into the directory this module lives in before running.

# Verify global + project-pinned tools (via go tool directives + mise).
# Go itself is project-pinned via mise, so every go invocation in
# this module goes through `mise exec --` — bare `go` breaks in any shell that
# hasn't run `mise activate`, which includes agent-run recipes.
# gocyclo/gocognit are probed with a plain path run: both exit 2 on -h (flag
# usage convention) but exit 0 on a real run without -over, findings or not.
[no-cd]
preflight:
    @echo "=== refactor::preflight (go) ==="
    @echo "--- Global ---"
    @scc --version
    @jscpd --version
    @semgrep --version
    @gitleaks version
    @osv-scanner --version
    @git --version
    @echo ""
    @echo "--- Project (via mise) ---"
    @mise exec -- go version
    @mise exec -- golangci-lint --version
    @echo ""
    @echo "--- Project (via go tool) ---"
    @mise exec -- go tool gocyclo . > /dev/null
    @mise exec -- go tool gocognit . > /dev/null
    @mise exec -- go tool goda help > /dev/null
    @mise exec -- go tool deadcode -h > /dev/null 2>&1
    @mise exec -- go tool govulncheck -version
    @mise exec -- go tool gosec -version

# Contract conformance via golangci-lint's depguard rules.
[no-cd]
architecture:
    @echo "=== refactor::architecture (go) ==="
    @mise exec -- golangci-lint run --disable-all --enable=depguard ./...

# Dependency graph: package-level edges and module-level edges.
[no-cd]
deps:
    @echo "=== refactor::deps (go) ==="
    @echo "--- goda graph (package edges) ---"
    @mise exec -- go tool goda graph ./...
    @echo ""
    @echo "--- go mod graph (first 50 module edges) ---"
    @mise exec -- go mod graph | head -n 50

# Per-function complexity: cyclomatic + cognitive.
[no-cd]
complexity:
    @echo "=== refactor::complexity (go) ==="
    @echo "--- gocyclo (CCN >= 10) ---"
    @mise exec -- go tool gocyclo -over 10 .
    @echo ""
    @echo "--- gocognit (cognitive >= 10) ---"
    @mise exec -- go tool gocognit -over 10 .

# Dead code.
[no-cd]
dead-code:
    @echo "=== refactor::dead-code (go) ==="
    @mise exec -- go tool deadcode ./...

# Lint-debt density via golangci-lint's full ruleset.
[no-cd]
lint-debt:
    @echo "=== refactor::lint-debt (go) ==="
    @mise exec -- golangci-lint run ./...

# Type-check (Go is strict by default; folds into compilation).
[no-cd]
types:
    @echo "=== refactor::types (go) ==="
    @echo "(Go: strict by default; type-check folds into compilation)"
    @mise exec -- go build ./...

# Known-vuln scan + security smell.
# osv-scanner (OSV.dev) complements govulncheck — govulncheck only flags
# vulns actually reachable from the call graph, osv-scanner flags every
# vulnerable dep version; together they cover "what's reachable now" and
# "what could be reached after the next refactor."
[no-cd]
security:
    @echo "=== refactor::security (go) ==="
    @echo "--- govulncheck (reachable from call graph) ---"
    @mise exec -- go tool govulncheck ./... || true
    @echo ""
    @echo "--- gosec ---"
    @mise exec -- go tool gosec ./... || true
    @echo ""
    @echo "--- osv-scanner (OSV.dev, every vulnerable dep version) ---"
    @osv-scanner scan source . || true

# Test suite + coverage.
[no-cd]
tests:
    @echo "=== refactor::tests (go) ==="
    @mise exec -- go test -cover ./...

# Install the audit's dev-tool requirements into the project (operator-invoked).
[no-cd]
install:
    @echo "=== refactor::install (go) ==="
    mise use golangci-lint@latest
    mise exec -- go get -tool github.com/fzipp/gocyclo/cmd/gocyclo@latest
    mise exec -- go get -tool github.com/uudashr/gocognit/cmd/gocognit@latest
    mise exec -- go get -tool github.com/loov/goda@latest
    mise exec -- go get -tool golang.org/x/tools/cmd/deadcode@latest
    mise exec -- go get -tool golang.org/x/vuln/cmd/govulncheck@latest
    mise exec -- go get -tool github.com/securego/gosec/v2/cmd/gosec@latest
    mise exec -- go mod tidy
    @if [ -e .jscpd.json ]; then echo ".jscpd.json present — leaving it untouched"; else cp "{{ tpl }}/jscpd.json" .jscpd.json && echo "dropped default .jscpd.json (baseline duplication ignores; extend per project)"; fi
