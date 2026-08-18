---
name: survey
description: Use when asked to survey a repo — bring its README, CLAUDE.md files, and Claude's memories about the project back in sync with reality after drift. One pass that audits all three artifact types against the current repo state and applies approved updates.
---

# Survey

Bring a repo's documentation artifacts back in line with what the repo actually is today. Three artifact types, one pass: `README.md` (operator-facing), `CLAUDE.md` files (Claude-facing), and this project's memory files. These drift because nothing forces them to update when code changes — survey is the periodic correction.

Run from the repo root of the project being surveyed.

## Step 1 — Establish drift window

Find out how stale each artifact is before reading it, so you know what to check hardest:

```bash
git log -1 --format='%ad %h' --date=short -- README.md
git log -1 --format='%ad %h' --date=short -- CLAUDE.md .claude/CLAUDE.md
git log --oneline --since="<older of the two dates>" | head -50
```

The commits since an artifact's last touch are the prime suspects for undocumented change. Also skim the repo shape (`ls`, the `justfile` if present, package manifests) for the current command surface and structure.

## Step 2 — Audit the docs (delegate)

Dispatch the `review:arcc-review` agent scoped to `README.md` and every `CLAUDE.md` in the repo. It verifies each claim against the repo (paths, commands, lists, configs), classifies content by audience, and returns a structured findings report. Do not re-derive its checks inline — it owns the doc-review standards.

Pass it the drift window from Step 1 so it knows which claims are most suspect.

If the agent is unavailable, fall back to verifying inline: every path, command, filename, and enumerated list in each doc gets checked against the working tree, and content is judged against its audience (README = operator setup and inventory; CLAUDE.md = operational rules Claude needs mid-task).

## Step 3 — Audit the memories (inline)

Your memory directory for this project is stated in your system prompt ("You have a persistent file-based memory at ..."). Read `MEMORY.md` and every memory file it indexes.

For each memory, verify what is checkable:

- **Named files, functions, flags, commands, paths** — confirm they still exist in the repo. A memory recommending a thing that's gone is stale.
- **Claims about project state** ("X is pending", "decision not yet made") — check whether the repo or backlog has since resolved them.
- **`user` and `feedback` memories** — usually not repo-checkable; leave them unless they reference something verifiably gone.

Also check the reverse direction: does `MEMORY.md` index every file present, and does every index line point at a file that exists?

Classify each: **current** (leave alone), **stale** (update in place), **wrong/obsolete** (delete, and remove its index line).

## Step 4 — Report, then apply

Present one combined report grouped by artifact: what's wrong, why (the evidence), and the proposed edit. Lead with a one-paragraph summary of overall drift.

Then apply, with different rules per artifact type:

- **Memories** — yours to fix. Update, delete, and re-index directly; note what you did in the report.
- **README / CLAUDE.md** — repo files under the repo's normal version-control rules. Get the operator's go-ahead on the proposed edits, make them on an appropriate branch per the repo's workflow, and never land on main without their explicit approval.

Scope discipline: survey updates artifacts to match reality — it does not fix the code, restructure docs wholesale, or invent new documentation. If the audit surfaces a real problem in the repo itself, file a draft backlog issue (or flag it in the report if the repo has no backlog) rather than expanding the survey.
