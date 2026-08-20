#!/usr/bin/env python3
# ABOUTME: Validates an OKF v0.2 knowledge bundle (design or docs kind) against its doctrine's mechanical invariants.
# ABOUTME: Usage: python3 lint_bundle.py [--kind design|docs] <bundle-dir>  (e.g. design/ or docs/)
"""
Lints a knowledge bundle so the atlas skills catch format drift before
committing. One script, two bundle kinds sharing one substrate:

`--kind design` (default; see references/wayfinding.md — used by /atlas:widen
and /atlas:deepen):
  - Every concept (non-reserved .md) carries parseable frontmatter with a known
    `type` (Map, Decision, Research, Prototype, Task). Files inside a
    `*.prototype/` directory are prototype artifacts, not concepts — skipped.
  - The bundle root has index.md pinning okf_version "0.2" and a map.md; every
    map has a non-empty Destination.
  - Maps use only the skeleton sections, omit empty sections, keep Regions and
    Frontier entries as bare links, and annotate Blocked / Decisions-so-far
    entries; state-section links must resolve.
  - No concept carries OKF `status` (waypoint lifecycle lives in maps).
  - A filled `## Decision` requires a `human:` verifier — the smuggled-
    resolution catch.
  - Filled `## Findings` require `sources`; footnote labels must match
    sources[].id; every source names a resource.
  - log.md is banned — history lives in git.

`--kind docs` (used by /atlas:document):
  - Machine-authored concepts carry one of the code-derivable types (Module,
    Helper, CLI, Playbook, DataModel, API) and a `sources` list; human-authored
    concepts (`generated.by` is `human:<id>`) may carry any type and need no
    sources — crafted prose is not a function of the code.
  - `generated` is required on every concept: the ownership rule (rewrite
    machine concepts, verify-and-flag human ones) keys off its actor.
  - OKF lifecycle is live: `status` must be draft|stable|deprecated when
    present; `stale_after` must be an absolute YYYY-MM-DD date.
  - log.md is allowed (it is the bundle's update history); its `##` headings
    must be ISO dates and it carries no frontmatter. No map machinery.
  - Broken links are warnings only (OKF consumers tolerate them).
  - Symbol existence: backticked code symbols in concept bodies (`A.b()`,
    `f()`, `_private`) must exist in the repo the bundle documents — the
    source root is the bundle's parent. Dotted names whose head is a
    repo-defined Python class are checked by class membership (stdlib ast);
    everything else by word-boundary search over non-markdown source files.
    Errors on machine-authored concepts, warnings on human-authored ones
    (their fix path is flag-don't-fix). Deliberate mentions of nonexistent
    symbols (shorthand, "there is no X" notes) are waived in place:
    `<!-- symbols-ok: <sym> <sym> — reason -->`. The check stands down when
    the repo has no source files at all.

Exit status: 0 if no errors (warnings allowed), 1 if any errors, 2 on usage.
"""
from __future__ import annotations

import ast
import enum
import re
import sys
from dataclasses import dataclass
from pathlib import Path

OKF_VERSION = "0.2"
KNOWN_TYPES = {"Map", "Decision", "Research", "Prototype", "Task"}
DOCS_MACHINE_TYPES = {"Module", "Helper", "CLI", "Playbook", "DataModel", "API"}
STATUS_VALUES = {"draft", "stable", "deprecated"}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WAYPOINT_TYPES = KNOWN_TYPES - {"Map"}
MAP_SECTIONS = {
    "Destination", "Notes", "Regions", "Frontier", "Blocked",
    "Decisions so far", "Not yet specified", "Out of scope", "Issues cut",
}
BARE_LINK_SECTIONS = {"Regions", "Frontier"}
ANNOTATED_LINK_SECTIONS = {"Blocked", "Decisions so far"}
STATE_SECTIONS = BARE_LINK_SECTIONS | ANNOTATED_LINK_SECTIONS

INLINE_CODE_RE = re.compile(r"`([^`]+)`")
SYMBOL_DOTTED_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+(\(\))?$")
SYMBOL_CALL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\(\)$")
SYMBOL_PRIVATE_RE = re.compile(r"^_[A-Za-z][A-Za-z0-9_]*(\(\))?$")
SYMBOLS_OK_RE = re.compile(r"<!--\s*symbols-ok:(.*?)-->", re.DOTALL)
SYMBOL_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*(?:\(\))?")
# Backticked spans that look dotted but are files or hosts, not code symbols.
# Skipping here only suppresses a finding, so the list errs generous.
NON_SYMBOL_EXTS = {
    "adoc", "bash", "bat", "c", "cfg", "clj", "conf", "cpp", "cs", "css",
    "csv", "dart", "env", "erl", "ex", "example", "exs", "gif", "go",
    "gradle", "graphql", "h", "hcl", "hpp", "hs", "html", "ini", "ipynb",
    "java", "jl", "jpeg", "jpg", "js", "json", "jsonl", "jsx", "kt", "lock",
    "lua", "m", "md", "mjs", "mm", "mod", "nim", "php", "pl", "png",
    "proto", "ps1", "py", "r", "rb", "rs", "rst", "scala", "service", "sh",
    "sql", "sum", "svelte", "svg", "swift", "tf", "tmpl", "toml", "ts",
    "tsx", "txt", "vue", "xml", "yaml", "yml", "zig", "zsh",
}
HOSTNAME_TLDS = {
    "com", "dev", "edu", "example", "gov", "internal", "io", "local",
    "net", "org", "test",
}
SOURCE_SKIP_DIRS = {
    "node_modules", "__pycache__", ".venv", "venv",
    "build", "dist", "target", "vendor",
}
SOURCE_SKIP_EXTS = {
    ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".lock", ".pdf", ".png",
    ".svg", ".tar", ".webp", ".woff", ".woff2", ".zip",
}
# Prose formats are claims about the code, never definitions of it.
PROSE_EXTS = {".md", ".markdown", ".rst", ".adoc"}
MAX_SOURCE_FILE_BYTES = 1_000_000
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")

KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
LINK_RE = re.compile(r"\[([^\]^][^\]]*|)\]\(([^)]+)\)")
BULLET_LINK_RE = re.compile(r"^-\s+\[[^\]]+\]\([^)]+\)(.*)$")
FOOTNOTE_LABEL_RE = re.compile(r"\[\^([^\]]+)\]")
EXTERNAL_TARGET_RE = re.compile(r"^(https?:|mailto:|#)")


class Severity(enum.Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Finding:
    severity: Severity
    path: Path
    line: int
    rule: str
    message: str


# --- Frontmatter: a restricted YAML subset (scalars, inline maps/lists, ---
# --- block lists of scalars / inline maps / block maps). No dependencies. ---

def _scalar(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def _flow_value(text: str) -> tuple[object, str | None]:
    if text.startswith("{"):
        if not text.endswith("}"):
            return None, f"unterminated inline mapping: {text!r}"
        result: dict[str, str] = {}
        inner = text[1:-1].strip()
        if inner:
            for part in inner.split(","):
                if ":" not in part:
                    return None, f"malformed inline mapping entry: {part.strip()!r}"
                key, value = part.split(":", 1)
                result[key.strip()] = _scalar(value)
        return result, None
    if text.startswith("["):
        if not text.endswith("]"):
            return None, f"unterminated inline list: {text!r}"
        inner = text[1:-1].strip()
        return ([_scalar(p) for p in inner.split(",")] if inner else []), None
    return _scalar(text), None


def _block_list(lines: list[str], start: int) -> tuple[list[object] | None, int, str | None]:
    items: list[object] = []
    dash_indent: int | None = None
    i = start
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0:
            break
        stripped = raw.strip()
        if stripped.startswith("- "):
            if dash_indent is None:
                dash_indent = indent
            if indent != dash_indent:
                return None, i, f"inconsistent list indentation: {raw!r}"
            rest = stripped[2:].strip()
            key_match = KEY_RE.match(rest)
            if rest.startswith(("{", "[")):
                value, err = _flow_value(rest)
                if err:
                    return None, i, err
                items.append(value)
            elif key_match:
                items.append({key_match.group(1): _scalar(key_match.group(2))})
            else:
                items.append(_scalar(rest))
        elif dash_indent is not None and indent > dash_indent:
            key_match = KEY_RE.match(stripped)
            if not key_match or not items or not isinstance(items[-1], dict):
                return None, i, f"malformed list continuation: {raw!r}"
            items[-1][key_match.group(1)] = _scalar(key_match.group(2))
        else:
            return None, i, f"malformed block value line: {raw!r}"
        i += 1
    if not items:
        return None, i, "block key with no value"
    return items, i, None


def parse_frontmatter(lines: list[str]) -> tuple[dict | None, str | None]:
    """Parse the delimited frontmatter lines (delimiters excluded)."""
    data: dict[str, object] = {}
    i = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        if raw[0] in " \t":
            return None, f"unexpected indentation: {raw!r}"
        key_match = KEY_RE.match(raw)
        if not key_match:
            return None, f"unparseable line: {raw!r}"
        key, rest = key_match.group(1), key_match.group(2).strip()
        if rest == "":
            value, i, err = _block_list(lines, i + 1)
            if err:
                return None, err
            data[key] = value
            continue
        value, err = _flow_value(rest)
        if err:
            return None, err
        data[key] = value
        i += 1
    return data, None


def split_document(text: str) -> tuple[list[str] | None, list[str], int, str | None]:
    """Split into (frontmatter_lines, body_lines, body_offset, error)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines, 0, None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return lines[1:idx], lines[idx + 1:], idx + 1, None
    return None, lines, 0, "frontmatter opened but never closed"


@dataclass
class Section:
    line: int
    content: list[str]


def parse_sections(body: list[str], offset: int) -> dict[str, Section]:
    sections: dict[str, Section] = {}
    current: Section | None = None
    for lineno, raw in enumerate(body, start=offset + 1):
        match = SECTION_RE.match(raw)
        if match:
            current = Section(line=lineno, content=[])
            sections[match.group(1)] = current
        elif current is not None:
            current.content.append(raw)
    return sections


def section_text(section: Section | None) -> str:
    if section is None:
        return ""
    return "\n".join(section.content).strip()


def strip_code(text: str) -> str:
    """Drop fenced code blocks and inline code spans, where regex character
    classes like `[^\\w-]` would otherwise read as footnote labels."""
    lines, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return re.sub(r"`[^`]*`", "", "\n".join(lines))


def fence_free_lines(lines: list[str], start: int):
    """Yield (lineno, raw) for lines outside fenced code blocks.

    Fences open on a run of 3+ backticks or tildes and close only on a run of
    the same character at least as long (so nested shorter fences stay
    inside). Per CommonMark, an unclosed fence runs to end of body.
    """
    fence: tuple[str, int] | None = None
    for lineno, raw in enumerate(lines, start=start):
        match = FENCE_RE.match(raw)
        if match:
            run = match.group(1)
            if fence is None:
                fence = (run[0], len(run))
                continue
            if run[0] == fence[0] and len(run) >= fence[1] \
                    and not raw.strip().strip(run[0]):
                fence = None
                continue
        if fence is None:
            yield lineno, raw


def code_free_lines(lines: list[str], start: int):
    """Yield (lineno, line) outside fences, with inline code spans removed."""
    for lineno, raw in fence_free_lines(lines, start):
        yield lineno, re.sub(r"`[^`]*`", "", raw)


class SourceCorpus:
    """Symbol-existence oracle over the repo a docs bundle documents.

    Two views of the same tree: the text of every source file (word-boundary
    existence for any name), and a class -> members map built with stdlib ast
    from the Python files (strict membership for dotted names whose head is a
    repo-defined class — the check a text search cannot make). Excluded from
    the corpus: the bundle itself, prose formats (docs are claims, not
    definitions), dot-paths, dependency/build directories, symlinks,
    binaries, and files over 1 MB.
    """

    def __init__(self, repo: Path, bundle: Path) -> None:
        self._members: dict[str, set[str]] = {}
        self._bases: dict[str, list[str]] = {}
        self._name_cache: dict[str, bool] = {}
        self.files = 0
        self.unreadable: list[Path] = []
        texts: list[str] = []
        for path in sorted(repo.rglob("*")):
            if not path.is_file() or path.is_symlink() \
                    or path.suffix.lower() in SOURCE_SKIP_EXTS \
                    or path.suffix.lower() in PROSE_EXTS:
                continue
            # Classify by the unresolved path: rglob results always sit under
            # repo, while resolving can follow a symlink out of it entirely.
            rel_parts = path.relative_to(repo).parts
            if path.is_relative_to(bundle) \
                    or any(p.startswith(".") or p in SOURCE_SKIP_DIRS for p in rel_parts):
                continue
            try:
                if path.stat().st_size > MAX_SOURCE_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                self.unreadable.append(path)
                continue
            self.files += 1
            texts.append(text)
            if path.suffix == ".py":
                self._index_python(text)
        self.text = "\n".join(texts)

    @property
    def empty(self) -> bool:
        return self.files == 0

    def _index_python(self, text: str) -> None:
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError, RecursionError):
            return
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            members = self._members.setdefault(node.name, set())
            bases = self._bases.setdefault(node.name, [])
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
                else:
                    bases.append("?")  # subscripted/dynamic base: unresolvable
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    members.add(child.name)
                elif isinstance(child, ast.Assign):
                    members.update(t.id for t in child.targets if isinstance(t, ast.Name))
                elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    members.add(child.target.id)
            # instance attributes: self.<name> = ... anywhere in the class's methods
            for sub in ast.walk(node):
                if isinstance(sub, ast.Attribute) and isinstance(sub.ctx, ast.Store) \
                        and isinstance(sub.value, ast.Name) and sub.value.id == "self":
                    members.add(sub.attr)

    def class_members(self, name: str) -> tuple[set[str], bool] | None:
        """Resolve a repo-defined class's members through its repo-defined
        bases. `complete` is False when any base (transitively) is not defined
        in the repo, so the index cannot claim authority over what the class
        inherits. None: not a repo class at all.
        """
        if name not in self._members:
            return None
        members: set[str] = set()
        complete = True
        stack, seen = [name], set()
        while stack:
            cls = stack.pop()
            if cls in seen or cls == "object":
                continue
            seen.add(cls)
            if cls not in self._members:
                complete = False
                continue
            members |= self._members[cls]
            stack.extend(self._bases.get(cls, []))
        return members, complete

    def has_name(self, name: str) -> bool:
        if name not in self._name_cache:
            self._name_cache[name] = re.search(
                rf"\b{re.escape(name)}\b", self.text) is not None
        return self._name_cache[name]


def symbol_candidate(span: str) -> str | None:
    """Classify a backticked span: return the normalized symbol, or None."""
    span = span.strip()
    if not (SYMBOL_DOTTED_RE.match(span) or SYMBOL_CALL_RE.match(span)
            or SYMBOL_PRIVATE_RE.match(span)):
        return None
    normalized = span.removesuffix("()")
    parts = normalized.split(".")
    if len(parts) > 1:
        if parts[-1].lower() in NON_SYMBOL_EXTS:
            return None  # a file name, not a symbol
        if parts[-1] in HOSTNAME_TLDS \
                and all(re.fullmatch(r"[a-z][a-z0-9-]*", p) for p in parts):
            return None  # a hostname, not a symbol
    return normalized


def symbol_waivers(body: list[str]) -> set[str]:
    """Collect symbols waived via `<!-- symbols-ok: <sym> <sym> — reason -->`.

    Collection stops at the first token that is not symbol-shaped, so a
    reason clause can never silently waive symbols it happens to mention.
    """
    waived: set[str] = set()
    for match in SYMBOLS_OK_RE.finditer("\n".join(body)):
        listing = re.split(r"—|--", match.group(1), maxsplit=1)[0]
        for token in SYMBOL_TOKEN_RE.findall(listing):
            if symbol_candidate(token) is None:
                break
            waived.add(token.removesuffix("()"))
    return waived


class BundleLinter:
    def __init__(self, bundle: Path, kind: str = "design") -> None:
        self.bundle = bundle
        self.kind = kind
        self.corpus: SourceCorpus | None = None
        self.findings: list[Finding] = []

    def add(self, severity: Severity, path: Path, line: int, rule: str, message: str) -> None:
        self.findings.append(Finding(severity, path, line, rule, message))

    def error(self, path: Path, line: int, rule: str, message: str) -> None:
        self.add(Severity.ERROR, path, line, rule, message)

    def warning(self, path: Path, line: int, rule: str, message: str) -> None:
        self.add(Severity.WARNING, path, line, rule, message)

    # --- per-file dispatch ---

    def run(self) -> list[Finding]:
        if self.kind == "docs":
            self.corpus = SourceCorpus(self.bundle.parent, self.bundle)
            for skipped in self.corpus.unreadable:
                self.warning(skipped, 1, "unreadable-source",
                             "source file could not be read, so it is missing from the "
                             "symbol-existence corpus — unknown-symbol findings may be "
                             "false until it is readable.")
        root_index = self.bundle / "index.md"
        if not root_index.is_file():
            self.error(root_index, 1, "missing-index",
                       f"bundle root needs an index.md pinning okf_version \"{OKF_VERSION}\".")
        if self.kind == "design":
            root_map = self.bundle / "map.md"
            if not root_map.is_file():
                self.error(root_map, 1, "missing-root-map",
                           "bundle root needs a map.md — the root map is the bundle's entry point.")
        for path in sorted(self.bundle.rglob("*.md")):
            if any(part.endswith(".prototype") for part in path.parent.parts):
                continue  # prototype artifacts are throwaway builds, not concepts
            name = path.name
            if name == "index.md":
                self.lint_index(path)
            elif name == "log.md":
                if self.kind == "design":
                    self.error(path, 1, "log-file",
                               "log.md is banned in the design bundle — there is no session log; "
                               "history lives in git.")
                else:
                    self.lint_log(path)
            elif self.kind == "docs":
                self.lint_docs_concept(path)
            else:
                self.lint_concept(path)
        return self.findings

    def lint_log(self, path: Path) -> None:
        lines = path.read_text().splitlines()
        if lines and lines[0].strip() == "---":
            self.error(path, 1, "log-frontmatter",
                       "log.md is a reserved file and carries no frontmatter (OKF §9).")
            return
        for lineno, raw in enumerate(lines, start=1):
            match = SECTION_RE.match(raw)
            if match and not ISO_DATE_RE.match(match.group(1)):
                self.error(path, lineno, "log-heading-not-date",
                           f"log.md headings are ISO dates (YYYY-MM-DD), got {match.group(1)!r} — "
                           "the log is a chronological record, newest first.")

    def lint_index(self, path: Path) -> None:
        fm_lines, _body, _offset, err = split_document(path.read_text())
        if err:
            self.error(path, 1, "unparseable-frontmatter", err)
            return
        is_root = path.parent == self.bundle
        if fm_lines is None:
            if is_root:
                self.error(path, 1, "missing-okf-version",
                           f"root index.md must pin okf_version \"{OKF_VERSION}\" in frontmatter.")
            return
        data, parse_err = parse_frontmatter(fm_lines)
        if parse_err or data is None:
            self.error(path, 1, "unparseable-frontmatter", parse_err or "empty frontmatter")
            return
        if not is_root or set(data) != {"okf_version"}:
            self.error(path, 1, "index-extra-keys",
                       "index.md frontmatter is allowed only at the bundle root, "
                       "and only the okf_version key.")
            if not is_root or "okf_version" not in data:
                return
        if is_root and data.get("okf_version") != OKF_VERSION:
            self.error(path, 1, "wrong-okf-version",
                       f"okf_version is {data.get('okf_version')!r}; this doctrine pins \"{OKF_VERSION}\". "
                       "Upgrades are a deliberate, operator-approved act.")

    def lint_concept(self, path: Path) -> None:
        text = path.read_text()
        fm_lines, body, offset, err = split_document(text)
        if err:
            self.error(path, 1, "unparseable-frontmatter", err)
            return
        if fm_lines is None:
            self.error(path, 1, "missing-frontmatter",
                       "every concept is an OKF document: YAML frontmatter with a type, then the body.")
            return
        data, parse_err = parse_frontmatter(fm_lines)
        if parse_err or data is None:
            self.error(path, 1, "unparseable-frontmatter", parse_err or "empty frontmatter")
            return

        ctype = data.get("type")
        if not ctype or not isinstance(ctype, str):
            self.error(path, 1, "missing-type", "frontmatter must carry a non-empty `type`.")
            return
        if ctype not in KNOWN_TYPES:
            self.error(path, 1, "unknown-type",
                       f"type {ctype!r} is not a design-bundle type ({', '.join(sorted(KNOWN_TYPES))}).")
            return

        if (ctype == "Map") != (path.name == "map.md"):
            self.error(path, 1, "map-filename",
                       "a map is exactly `<dir>/map.md` with `type: Map` — "
                       f"got type {ctype!r} in {path.name!r}.")

        if "status" in data:
            self.error(path, 1, "status-key",
                       "OKF `status` is not used in the design bundle: waypoint lifecycle lives "
                       "in the nearest enclosing map's sections, nowhere else.")

        human_verified = self.check_trust(path, data)
        sections = parse_sections(body, offset)
        self.check_links(path, ctype, sections)
        for name, section in sections.items():
            if not section_text(section):
                self.error(path, section.line, "empty-section",
                           f"section {name!r} is empty — empty sections are omitted.")

        if ctype == "Map":
            self.lint_map(path, sections)
        else:
            self.lint_waypoint(path, ctype, data, sections, human_verified)

    # --- docs concepts ---

    def lint_docs_concept(self, path: Path) -> None:
        text = path.read_text()
        fm_lines, body, offset, err = split_document(text)
        if err:
            self.error(path, 1, "unparseable-frontmatter", err)
            return
        if fm_lines is None:
            self.error(path, 1, "missing-frontmatter",
                       "every concept is an OKF document: YAML frontmatter with a type, then the body.")
            return
        data, parse_err = parse_frontmatter(fm_lines)
        if parse_err or data is None:
            self.error(path, 1, "unparseable-frontmatter", parse_err or "empty frontmatter")
            return

        ctype = data.get("type")
        if not ctype or not isinstance(ctype, str):
            self.error(path, 1, "missing-type", "frontmatter must carry a non-empty `type`.")
            return

        generated = data.get("generated")
        if generated is None:
            self.error(path, 1, "missing-generated",
                       "docs concepts must carry `generated: { by, at }` — the ownership rule "
                       "(rewrite machine concepts, verify-and-flag human ones) keys off the actor.")
        elif not (isinstance(generated, dict) and generated.get("by") and generated.get("at")):
            self.error(path, 1, "malformed-generated",
                       "`generated` must be an inline mapping with `by` and `at`.")
        by = generated.get("by", "") if isinstance(generated, dict) else ""
        human_authored = str(by).startswith("human:")

        if not human_authored and ctype not in DOCS_MACHINE_TYPES:
            self.error(path, 1, "unknown-type",
                       f"type {ctype!r} is not a code-derivable docs type "
                       f"({', '.join(sorted(DOCS_MACHINE_TYPES))}). Human-authored concepts "
                       "(generated.by human:<id>) may carry their own types.")

        self.check_verified(path, data)

        has_sources, source_ids = self.check_sources(path, data)
        if not human_authored and not has_sources:
            self.error(path, 1, "machine-concept-without-sources",
                       "machine-authored docs concepts derive from the code and record that "
                       "provenance in `sources` — without it, staleness cannot be scoped by git.")

        status = data.get("status")
        if status is not None and status not in STATUS_VALUES:
            self.error(path, 1, "invalid-status",
                       f"`status` is OKF lifecycle: {' | '.join(sorted(STATUS_VALUES))}; got {status!r}.")

        stale_after = data.get("stale_after")
        if stale_after is not None and not ISO_DATE_RE.match(str(stale_after)):
            self.error(path, 1, "invalid-stale-after",
                       f"`stale_after` is an absolute YYYY-MM-DD date, got {stale_after!r} — "
                       "staleness stays a plain date comparison.")

        # Docs bodies have no section skeleton: check links and footnotes over raw
        # lines, skipping code — a link or footnote inside a fence or inline span
        # is example text, not a claim about the bundle.
        for lineno, line in code_free_lines(body, offset + 1):
            for match in LINK_RE.finditer(line):
                target = match.group(2).strip()
                if EXTERNAL_TARGET_RE.match(target):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                resolved = (self.bundle / target.lstrip("/")) if target.startswith("/") \
                    else (path.parent / target)
                if not resolved.exists():
                    self.warning(path, lineno, "broken-link",
                                 f"link target {match.group(2)!r} does not exist in the bundle.")
        body_text = strip_code("\n".join(body))
        for label in set(FOOTNOTE_LABEL_RE.findall(body_text)):
            if label not in source_ids:
                self.error(path, 1, "unmatched-footnote",
                           f"footnote label [^{label}] has no matching `sources` entry id — "
                           "the label is the join key into sources.")
        self.check_symbols(path, body, offset, human_authored)

    def check_symbols(self, path: Path, body: list[str], offset: int,
                      human_authored: bool) -> None:
        """Every backticked code symbol must exist in the documented repo."""
        if self.corpus is None or self.corpus.empty:
            return
        waived = symbol_waivers(body)
        reported: set[str] = set()
        severity = Severity.WARNING if human_authored else Severity.ERROR
        for lineno, raw in fence_free_lines(body, offset + 1):
            for span in INLINE_CODE_RE.findall(raw):
                symbol = symbol_candidate(span)
                if symbol is None or symbol in waived or symbol in reported:
                    continue
                parts = symbol.split(".")
                resolved = self.corpus.class_members(parts[0]) if len(parts) > 1 else None
                if resolved is not None:
                    members, complete = resolved
                    # Only the immediate member is statically checkable: in
                    # `A.b.c`, `c` belongs to whatever `b` is, not to `A`.
                    if parts[1] in members:
                        continue
                    # A class with a base outside the repo may inherit members
                    # the index cannot see: the text corpus decides instead.
                    if not complete and self.corpus.has_name(parts[1]):
                        continue
                    detail = f"class `{parts[0]}` defines no member `{parts[1]}`"
                else:
                    if self.corpus.has_name(parts[-1]):
                        continue
                    detail = "it has no match in the repo's source files"
                reported.add(symbol)
                self.add(severity, path, lineno, "unknown-symbol",
                         f"`{symbol}`: {detail} — fabricated, renamed, or shorthand? "
                         "A deliberate mention of a nonexistent symbol is waived with "
                         f"`<!-- symbols-ok: {symbol} — reason -->`.")

    # --- trust family ---

    def check_trust(self, path: Path, data: dict) -> bool:
        """Validate generated/verified shapes; return whether a human verifier exists."""
        generated = data.get("generated")
        if generated is None:
            self.warning(path, 1, "missing-generated",
                         "concept has no `generated: { by, at }` — sessions stamp what they write.")
        elif not (isinstance(generated, dict) and generated.get("by") and generated.get("at")):
            self.error(path, 1, "malformed-generated",
                       "`generated` must be an inline mapping with `by` and `at`.")
        return self.check_verified(path, data)

    def check_verified(self, path: Path, data: dict) -> bool:
        """Validate the `verified` shape; return whether a human verifier exists."""
        verified = data.get("verified")
        entries: list[object]
        if verified is None:
            entries = []
        elif isinstance(verified, dict):
            entries = [verified]
        elif isinstance(verified, list):
            entries = verified
        else:
            self.error(path, 1, "malformed-verified",
                       "`verified` must be a { by, at } mapping or a list of them.")
            return False
        human = False
        for entry in entries:
            if not (isinstance(entry, dict) and entry.get("by") and entry.get("at")):
                self.error(path, 1, "malformed-verified",
                           "each `verified` entry needs both `by` and `at`.")
            if isinstance(entry, dict) and str(entry.get("by", "")).startswith("human:"):
                human = True
        return human

    def check_sources(self, path: Path, data: dict) -> tuple[bool, set[str]]:
        """Validate the `sources` shape; return (present, footnote-joinable ids)."""
        sources = data.get("sources")
        source_ids: set[str] = set()
        if sources is None:
            return False, source_ids
        if not isinstance(sources, list):
            self.error(path, 1, "source-missing-resource",
                       "`sources` must be a list of entries, each with a `resource`.")
            return True, source_ids
        for entry in sources:
            if not isinstance(entry, dict) or not entry.get("resource"):
                self.error(path, 1, "source-missing-resource",
                           "every `sources` entry names a `resource` (URL, path, or scope).")
            if isinstance(entry, dict) and entry.get("id"):
                source_ids.add(str(entry["id"]))
        return True, source_ids

    # --- links ---

    def check_links(self, path: Path, ctype: str, sections: dict[str, Section]) -> None:
        for name, section in sections.items():
            in_state = ctype == "Map" and name in STATE_SECTIONS
            for lineno, line in code_free_lines(section.content, section.line + 1):
                for match in LINK_RE.finditer(line):
                    target = match.group(2).strip()
                    if EXTERNAL_TARGET_RE.match(target):
                        continue
                    target = target.split("#", 1)[0]
                    if not target:
                        continue
                    resolved = (self.bundle / target.lstrip("/")) if target.startswith("/") \
                        else (path.parent / target)
                    if not resolved.exists():
                        severity = Severity.ERROR if in_state else Severity.WARNING
                        self.add(severity, path, lineno, "broken-link",
                                 f"link target {match.group(2)!r} does not exist in the bundle.")

    # --- maps ---

    def lint_map(self, path: Path, sections: dict[str, Section]) -> None:
        for name, section in sections.items():
            if name not in MAP_SECTIONS:
                self.error(path, section.line, "unknown-section",
                           f"map section {name!r} is not in the skeleton "
                           f"({', '.join(sorted(MAP_SECTIONS))}).")
        destination = sections.get("Destination")
        if destination is None or not section_text(destination):
            self.error(path, 1, "missing-destination", "every map has a `## Destination`.")

        for name in BARE_LINK_SECTIONS & sections.keys():
            section = sections[name]
            for lineno, raw in enumerate(section.content, start=section.line + 1):
                stripped = raw.strip()
                if not stripped:
                    continue
                bullet = BULLET_LINK_RE.match(stripped)
                if not bullet or bullet.group(1).strip():
                    self.error(path, lineno, "annotated-entry",
                               f"{name} entries are bare links — no status prose, no annotations. "
                               "Whether a subtree is quiet is discovered by reading it.")
        for name in ANNOTATED_LINK_SECTIONS & sections.keys():
            section = sections[name]
            for lineno, raw in enumerate(section.content, start=section.line + 1):
                stripped = raw.strip()
                if not stripped:
                    continue
                bullet = BULLET_LINK_RE.match(stripped)
                if bullet and not bullet.group(1).strip():
                    detail = "the blocker" if name == "Blocked" else "a one-line gist of the answer"
                    self.error(path, lineno, "missing-annotation",
                               f"{name} entries carry {detail} after the link.")

    # --- waypoints ---

    def lint_waypoint(self, path: Path, ctype: str, data: dict,
                      sections: dict[str, Section], human_verified: bool) -> None:
        if not section_text(sections.get("Question")):
            self.error(path, 1, "missing-question",
                       f"a {ctype} waypoint states its `## Question` — one question, one decision.")

        if section_text(sections.get("Decision")) and not human_verified:
            self.error(path, 1, "smuggled-resolution",
                       "`## Decision` is filled but no `human:` actor appears in `verified` — "
                       "decisions are the operator's; record the confirmation or remove the text.")

        has_sources, source_ids = self.check_sources(path, data)

        if section_text(sections.get("Findings")) and not has_sources:
            self.error(path, 1, "findings-without-sources",
                       "`## Findings` is filled but frontmatter has no `sources` — "
                       "research claims carry their provenance.")

        body_text = strip_code(
            "\n".join(line for section in sections.values() for line in section.content))
        for label in set(FOOTNOTE_LABEL_RE.findall(body_text)):
            if label not in source_ids:
                self.error(path, 1, "unmatched-footnote",
                           f"footnote label [^{label}] has no matching `sources` entry id — "
                           "the label is the join key into sources.")


def lint(bundle_dir: Path, kind: str = "design") -> list[Finding]:
    return BundleLinter(Path(bundle_dir), kind).run()


def format_finding(f: Finding) -> str:
    return f"{f.path}:{f.line}: {f.severity.value.upper()} [{f.rule}]\n  {f.message}"


def main(argv: list[str]) -> int:
    usage = "Usage: lint_bundle.py [--kind design|docs] <bundle-dir>"
    args = argv[1:]
    kind = "design"
    if args[:1] == ["--kind"]:
        if len(args) < 2 or args[1] not in ("design", "docs"):
            print(usage, file=sys.stderr)
            return 2
        kind, args = args[1], args[2:]
    if len(args) != 1:
        print(usage, file=sys.stderr)
        return 2
    bundle_dir = Path(args[0])
    if not bundle_dir.is_dir():
        print(f"Not a directory: {bundle_dir}", file=sys.stderr)
        return 2
    findings = lint(bundle_dir, kind)
    for finding in findings:
        print(format_finding(finding))
        print()
    errors = sum(1 for f in findings if f.severity is Severity.ERROR)
    warnings = sum(1 for f in findings if f.severity is Severity.WARNING)
    print(f"lint_bundle: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
