---
name: fj
description: Claude-internal — Claude invokes this itself during its work; not useful to type directly. Use when interacting with Forgejo repositories via CLI — creating PRs, managing issues, releases, or CI status — or any time you'd reach for `gh` but the repo's remote is Forgejo (the default host) rather than GitHub.
---

# fj (Forgejo CLI)

`fj` is the CLI for Forgejo/Gitea instances. It is shaped like `gh`: same
verbs (`pr`, `issue`, `release`, `repo`, `actions`), same instincts mostly
transfer. It is self-documenting — `fj <command> --help` and
`fj <command> <subcommand> --help` give accurate, complete usage. Reach for
`--help` for anything not listed here.

This skill is **only** the delta: the places where `gh` muscle memory
produces a wrong `fj` command, or where the answer costs an agent a failed
round trip to discover. Verified against `fj v0.6.0`.

## Where `gh` instinct misleads you

- **Repo targeting is split, and `-R` is not what `gh` means by `-R`.**
  - `-R`/`--remote` = a **local git remote name** (e.g. `origin`), not `owner/repo`.
  - `-r`/`--repo` = the repo spec (e.g. `owner/name`).
  Using `gh`'s `-R owner/repo` habit on `fj` targets the wrong thing.
  And the flags are **per-subcommand, not uniform**: `issue`/`pr` `search`
  and `create` take `-r owner/repo` (so do the `wiki`, `actions`, `release`,
  and `tag` families), but the other `issue`/`pr` subcommands (`view`,
  `edit`, `close`, `comment`, `merge`, …) take no `-r`/`--repo` at all —
  passing it there errors (`unexpected argument`). Relying on the cwd's
  default remote works only when its host matches the API host; otherwise
  it errors `can't figure out what repo to access` — put the repo in the ID
  itself as `{owner}/{repo}#N` (e.g. `fj issue view owner/name#42`). Same
  form applies to `pr view`. One more trap: on `repo create` and
  `org repo create`, `-r`/`--remote` means "create a **local git remote**
  with this name for the new repo" — not a repo spec.
- **There is no `fj issue list` / `fj pr list`.** `gh`'s `list` verb is
  `search` here: `fj issue search -s all`, `fj pr search -s all`
  (`-s`: open (default) | closed | all). `search` with no query lists
  everything. `issue list` fails with `unrecognized subcommand 'list'`.
  **`search` output shows NO state** — just `#N: title (by author)`,
  identical for open and closed. So `-s all` cannot tell you which are
  closed (unlike `gh issue list`'s state column). To know state, run
  `-s open` / `-s closed` separately, or `fj issue view <N>` (which does
  print `Open`/`Closed`).
- **`-H`/`--host` goes anywhere — except `fj auth logout`.** Every other
  subcommand accepts `-H`, before
  or after the subcommand — `fj -H host.example issue create ...` and
  `fj issue create ... -H host.example` both work. `auth logout` alone takes
  the host as a **positional** and rejects the flag outright
  (`error: unexpected argument '-H' found`), which is doubly easy to trip
  over because its sibling `auth add-token` does accept `-H`.
  Needed only when `fj` can't resolve the API host — it errors
  `can't figure out what repo to access`. A remote whose host matches an
  instance you're logged into (`fj auth list`) resolves fine, including SSH
  on a non-standard port; reach for `-H` when the host is outside your
  authenticated instances.
- **`fj repo labels` targets a repo by positional `[REPO]`, not `-r`/`-R`.**
  The shape is `fj repo labels [REPO] <subcommand>` (e.g.
  `fj repo labels owner/name view`); it accepts neither `-r` nor `-R`
  (unlike `issue`/`pr`). Omit the positional only when the cwd's git remote
  resolves to `owner/name` — when the remote's SSH host differs from the API
  host, `fj` can't infer it and errors `couldn't get repo name, please
  specify`, so pass `[REPO]` explicitly. `-H` still works (global, before
  the subcommand).
- **Title is positional, not a flag.** `fj pr create "Title" ...` — there is
  no `--title`.
- **No `--draft`.** Mark a draft PR by prefixing the title: `"WIP: Title"`.
- **`view`/`edit` use a subcommand noun, not flags.**
  `fj pr view 42 diff`, `fj pr view 42 files`, `fj pr view 42 body`,
  `fj issue edit 7 title "New"`, `fj issue edit 7 labels -a foo -r bar`
  (`-r`/`--rm` removes; gh's word is `--remove`).
- **There is no `fj label` command.** Label *definitions* live under
  `fj repo labels` (`view`/`create`/`edit`/`delete`). `fj issue edit <n>
  labels -a <name>` only *attaches* an existing label to an issue — it does
  not create the definition, and fails if the label doesn't exist. And
  `issue create` has **no `--label` flag**: create the issue, then attach
  with `issue edit <n> labels -a <name>`.
- **Label `create` is not idempotent — use edit-or-create.**
  `fj repo labels [REPO] create <name> …` does **not** fail or upsert on a
  duplicate name; it silently creates a *second* label with that name.
  `edit <name>` instead fails cleanly (exit 1, `No label found with the
  given name`) when the label is absent and never creates it. To assert a
  label idempotently: try `edit` first, and `create` only when stderr
  contains `No label found` — never on any other error, or a
  transient/permission failure spawns a duplicate. This is the pattern to use
  for asserting a canonical label set idempotently.
- **Omitting a body opens `$EDITOR` and blocks the agent.** Always pass a
  body explicitly on anything that takes one:
  - `pr create` / `issue create`: `--body` / `--body-file` (the title is
    the positional arg; the body is **not** positional here)
  - `pr comment` / `issue comment`: body is the **positional** arg (no
    `--body` flag — passing `--body` errors) or `--body-file`
  - `pr close` / `issue close`: `-w`/`--with-msg "reason"` — and note `-w`
    with **no argument** also opens the editor.
  - `issue edit` / `pr edit` `title|body|comment`: omitting the new-value
    positional opens the current value in the editor.
  - Optional-argument flags passed bare do the same: `release create -b`,
    `tag create -b`, `pr merge -m`, and `actions variables create` with no
    DATA argument all open the editor.
- **fj output is not parser-safe.** Every interpolated field (usernames,
  titles, hosts, issue numbers) is wrapped in invisible Unicode directional
  isolates (U+2066–U+2069) in **all** fj output, and `--style minimal` does
  not strip them — a sed/grep parser matching `<user>@<host>` silently
  captures the isolates along with the value. Strip them before parsing:
  `perl -CS -pe 's/[\x{2066}-\x{2069}]//g'`. Wording is also gh-divergent
  where you'd parse it: `fj whoami` prints `currently signed into
  <user>@<host>` — "into", one word, not gh's "signed in to" — and `whoami`
  has no machine-readable output flag. (This pair of quirks silently breaks
  naive owner-detection parsers.)
- **There is no `fj api`.** `gh api` muscle memory has no equivalent here —
  when a subcommand looks missing, there is no raw-API escape hatch to fall
  back on; what the CLI exposes is all there is.
- **Version is `fj version`,** not `fj --version`.

## Commands that are gh-divergent enough to spell out

```bash
# PRs
fj pr create "Title" --base main --head feature --body "..."   # --base AND --head
fj pr create -A --base main                                    # -A/--autofill from commits
fj pr status 42 --wait                                         # block until checks finish
fj pr merge 42 -M squash -d -t "Title (#42)" -m "Body"         # -M method, -d deletes branch
#   -M methods: merge | rebase | rebase-merge | squash | manual
#   -t/-m set the merge/squash commit title and body; -m with NO argument opens the editor
fj pr review 42 list                                           # list reviews; -c adds inline
#   review comments, -a includes stale/dismissed reviews
fj pr search -s all                                            # -s: open (default) | closed | all
fj pr view 42 body|comment|comments|labels|assignees|diff|files|commits   # subcommand, not a flag

# Issues
fj issue edit 7 labels -a added -r removed                     # -a add, -r/--rm remove
#   ^ succeeds SILENTLY (no output). Don't assume failure; verify with `issue view`.
fj issue view 7                                                # labels shown in plain view
fj issue view 7 body|comment|comments|assignees                # body is the default; there is
#   NO `labels` subcommand (that's pr-only — `issue view 7 labels` errors); `comments`
#   lists every comment, `comment` views one
fj issue close 7 -w "reason"                                   # -w/--with-msg, inline arg required

# Labels — repo-level defs under `fj repo labels [REPO] <subcommand>` (NOT `fj label`)
fj repo labels owner/name view                                 # list existing labels
fj repo labels owner/name create state/approved a3b18a -e      # NAME then COLOR (hex); -e = exclusive
fj repo labels owner/name edit state/approved -c a3b18a -e true # edit by name/ID; on EDIT -e takes true|false
fj repo labels owner/name delete state/approved               # by name or ID
#   -d/--description with NO argument opens $EDITOR — omit it or pass a value.
#   -e is a BARE flag on create but true|false on edit. Exclusivity is per namespace —
#   the `scope` in a `scope/value` name (`scope:value` is NOT treated as a namespace).

# Org-level labels (one shared set across all the org's repos; user repos have no equivalent)
fj org label list|add|edit|rm                                  # define labels once on an organization

# Auth / identity
fj whoami            # current signed-in identity for the active instance
fj auth list         # all instances you're logged into
fj auth login        # opens browser (interactive — not agent-runnable)
fj auth add-token -H <host>   # agent-runnable fallback: token as arg or via stdin
#   Refuses to REPLACE a credential: with one already stored for that host it
#   fails `new key:key for <host> already exists`, leaves the old one in place,
#   and still exits 0 — so a switch that silently did nothing looks like it
#   worked. Verify with `fj whoami`, and log out first to change identity.
fj auth logout <host>         # HOST is POSITIONAL — `-H` errors here
```

Everything else (`release`, `tag`, `repo`, `actions`, `wiki`, plain
`view`/`search`/`comment`) behaves close enough to `gh` that
`fj <command> --help` is faster than prose here.
