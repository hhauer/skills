#!/usr/bin/env python3
# ABOUTME: Validates an OKF v0.2 design bundle against the wayfinding doctrine's mechanical invariants.
# ABOUTME: Usage: python3 lint_bundle.py <bundle-dir>  (e.g. design/)
"""
Lints a design bundle (see references/wayfinding.md) so /agentic-sdlc:wayfinding-widen
and /agentic-sdlc:wayfinding-deepen sessions catch format drift before committing.

Checked invariants:
  - Every concept (non-reserved .md) carries parseable frontmatter with a known
    `type` (Map, Decision, Research, Prototype, Task).
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

Exit status: 0 if no errors (warnings allowed), 1 if any errors, 2 on usage.
"""
from __future__ import annotations

import enum
import re
import sys
from dataclasses import dataclass
from pathlib import Path

OKF_VERSION = "0.2"
KNOWN_TYPES = {"Map", "Decision", "Research", "Prototype", "Task"}
WAYPOINT_TYPES = KNOWN_TYPES - {"Map"}
MAP_SECTIONS = {
    "Destination", "Notes", "Regions", "Frontier", "Blocked",
    "Decisions so far", "Not yet specified", "Out of scope", "Issues cut",
}
BARE_LINK_SECTIONS = {"Regions", "Frontier"}
ANNOTATED_LINK_SECTIONS = {"Blocked", "Decisions so far"}
STATE_SECTIONS = BARE_LINK_SECTIONS | ANNOTATED_LINK_SECTIONS

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


class BundleLinter:
    def __init__(self, bundle: Path) -> None:
        self.bundle = bundle
        self.findings: list[Finding] = []

    def add(self, severity: Severity, path: Path, line: int, rule: str, message: str) -> None:
        self.findings.append(Finding(severity, path, line, rule, message))

    def error(self, path: Path, line: int, rule: str, message: str) -> None:
        self.add(Severity.ERROR, path, line, rule, message)

    def warning(self, path: Path, line: int, rule: str, message: str) -> None:
        self.add(Severity.WARNING, path, line, rule, message)

    # --- per-file dispatch ---

    def run(self) -> list[Finding]:
        root_index = self.bundle / "index.md"
        if not root_index.is_file():
            self.error(root_index, 1, "missing-index",
                       f"bundle root needs an index.md pinning okf_version \"{OKF_VERSION}\".")
        root_map = self.bundle / "map.md"
        if not root_map.is_file():
            self.error(root_map, 1, "missing-root-map",
                       "bundle root needs a map.md — the root map is the bundle's entry point.")
        for path in sorted(self.bundle.rglob("*.md")):
            name = path.name
            if name == "index.md":
                self.lint_index(path)
            elif name == "log.md":
                self.error(path, 1, "log-file",
                           "log.md is banned in the design bundle — there is no session log; "
                           "history lives in git.")
            else:
                self.lint_concept(path)
        return self.findings

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

    # --- links ---

    def check_links(self, path: Path, ctype: str, sections: dict[str, Section]) -> None:
        for name, section in sections.items():
            in_state = ctype == "Map" and name in STATE_SECTIONS
            for lineno, raw in enumerate(section.content, start=section.line + 1):
                for match in LINK_RE.finditer(raw):
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

        sources = data.get("sources")
        source_ids: set[str] = set()
        if sources is not None:
            if not isinstance(sources, list):
                self.error(path, 1, "source-missing-resource",
                           "`sources` must be a list of entries, each with a `resource`.")
            else:
                for entry in sources:
                    if not isinstance(entry, dict) or not entry.get("resource"):
                        self.error(path, 1, "source-missing-resource",
                                   "every `sources` entry names a `resource` (URL, path, or scope).")
                    if isinstance(entry, dict) and entry.get("id"):
                        source_ids.add(str(entry["id"]))

        if section_text(sections.get("Findings")) and not sources:
            self.error(path, 1, "findings-without-sources",
                       "`## Findings` is filled but frontmatter has no `sources` — "
                       "research claims carry their provenance.")

        body_text = "\n".join(line for section in sections.values() for line in section.content)
        for label in set(FOOTNOTE_LABEL_RE.findall(body_text)):
            if label not in source_ids:
                self.error(path, 1, "unmatched-footnote",
                           f"footnote label [^{label}] has no matching `sources` entry id — "
                           "the label is the join key into sources.")


def lint(bundle_dir: Path) -> list[Finding]:
    return BundleLinter(Path(bundle_dir)).run()


def format_finding(f: Finding) -> str:
    return f"{f.path}:{f.line}: {f.severity.value.upper()} [{f.rule}]\n  {f.message}"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: lint_bundle.py <bundle-dir>", file=sys.stderr)
        return 2
    bundle_dir = Path(argv[1])
    if not bundle_dir.is_dir():
        print(f"Not a directory: {bundle_dir}", file=sys.stderr)
        return 2
    findings = lint(bundle_dir)
    for finding in findings:
        print(format_finding(finding))
        print()
    errors = sum(1 for f in findings if f.severity is Severity.ERROR)
    warnings = sum(1 for f in findings if f.severity is Severity.WARNING)
    print(f"lint_bundle: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
