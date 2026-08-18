# ABOUTME: Cross-language refactor-audit recipes. Imported by the language
# ABOUTME: modules beside it; never invoked directly. See review:refactor-audit
# ABOUTME: for how the modules are run.

# Every recipe in this family runs against the project that invoked just,
# not against the directory where this module file lives. `[no-cd]` keeps
# just from chdir'ing into the directory this module lives in before running.

# Size, language split, and repo markers — run first to calibrate downstream.
[no-cd]
orient:
    @echo "=== refactor::orient ==="
    @scc .
    @echo ""
    @echo "--- Repo markers ---"
    @ls -1 README* CHANGELOG* LICENSE* 2>/dev/null || true
    @ls -1 go.mod pyproject.toml setup.cfg package.json tsconfig.json 2>/dev/null || true

# Ignore scope lives in the project's .jscpd.json (dropped by refactor::install
# with a baseline that excludes non-source noise like openspec/, whose
# archive-sync produces spec-vs-archive clones that are not code; extend it per
# project). jscpd's CLI --ignore would *override* that file rather than merge,
# so this recipe deliberately passes no --ignore and lets jscpd auto-load the
# config. The console reporter emits clone locations only — no full clone bodies
# in ANSI boxes.
# Cross-language token-based duplication detection.
[no-cd]
duplication:
    @echo "=== refactor::duplication ==="
    @jscpd --reporters console .

# Deterministic smell rules (semgrep) and secret scan (gitleaks).
[no-cd]
security-scan:
    @echo "=== refactor::security-scan ==="
    @echo "--- semgrep (auto config) ---"
    @semgrep --config=auto --quiet --error || true
    @echo ""
    @echo "--- gitleaks (full history scan) ---"
    @gitleaks detect --no-banner --redact || true

# Behavioral history from git log — change frequency and recent activity.
# Excludes .beads/ (tracker metadata, not source) so the churn ranking
# reflects code activity, not bead-export commits.
[no-cd]
history:
    @echo "=== refactor::history: change-frequency top-30 (last 12mo) ==="
    @git log --since='12 months ago' --name-only --pretty=format: -- . ':!.beads' | grep -v '^$' | sort | uniq -c | sort -rn | head -n 30
    @echo ""
    @echo "=== refactor::history: files-touched (last 30d) ==="
    @git log --since='30 days ago' --name-only --pretty=format: -- . ':!.beads' | grep -v '^$' | sort -u
