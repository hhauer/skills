#!/usr/bin/env python3
# ABOUTME: Tests for lint_bundle.py — the OKF design-bundle linter used by the wayfinding skills.
# ABOUTME: Run with: python3 test_lint_bundle.py
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_bundle import Severity, lint  # noqa: E402


VALID_INDEX = """\
---
okf_version: "0.2"
---

# Design bundle

* [Root map](map.md) - start here
"""

VALID_ROOT_MAP = """\
---
type: Map
generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }
---

# Test Project

## Destination

A working test project.

## Notes

Operator actor id: human:tester
"""


class FixtureBase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="lint-bundle-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bundle = self.root / "design"
        self.bundle.mkdir()

    def write(self, rel: str, content: str) -> Path:
        path = self.bundle / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content))
        return path

    def write_valid_root(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("map.md", VALID_ROOT_MAP)

    def errors(self, findings):
        return [f for f in findings if f.severity is Severity.ERROR]

    def warnings(self, findings):
        return [f for f in findings if f.severity is Severity.WARNING]

    def rules(self, findings):
        return [f.rule for f in findings]


class TestCleanBundle(FixtureBase):
    def test_minimal_bundle_is_clean(self) -> None:
        self.write_valid_root()
        self.assertEqual(lint(self.bundle), [])

    def test_full_bundle_is_clean(self) -> None:
        self.write_valid_root()
        self.write("map.md", VALID_ROOT_MAP + textwrap.dedent("""\

            ## Regions

            - [billing](billing/map.md)

            ## Decisions so far

            - [auth-provider](auth-provider.md) — use Clerk

            ## Not yet specified

            Something about exports, once billing resolves.
            """))
        self.write("auth-provider.md", """\
            ---
            type: Decision
            generated: { by: claude-code/test-model, at: 2026-08-01T10:00:00Z }
            verified: { by: human:tester, at: 2026-08-01T10:05:00Z }
            ---

            # auth-provider

            ## Question

            Which auth provider do we build on?

            ## Decision

            Clerk, because it removes session management entirely.
            """)
        self.write("billing/map.md", """\
            ---
            type: Map
            generated: { by: claude-code/test-model, at: 2026-08-02T10:00:00Z }
            ---

            # Billing

            ## Destination

            Billing design resolved end to end.

            ## Frontier

            - [billable-event](billable-event.md)

            ## Blocked

            - [invoice-format](invoice-format.md) — waits on [billable-event](billable-event.md)
            """)
        self.write("billing/billable-event.md", """\
            ---
            type: Research
            generated: { by: waypoint-researcher/test-model, at: 2026-08-02T11:00:00Z }
            sources:
              - id: stripe-metering
                resource: https://docs.stripe.com/billing/subscriptions/usage-based
                title: Stripe usage-based billing
            ---

            # billable-event

            ## Question

            What is the billable event?

            ## Findings

            Stripe meters usage per event record.[^stripe-metering]

            [^stripe-metering]: Stripe usage-based billing
            """)
        self.write("billing/invoice-format.md", """\
            ---
            type: Decision
            generated: { by: claude-code/test-model, at: 2026-08-02T10:00:00Z }
            ---

            # invoice-format

            ## Question

            What does the invoice line-item format look like?
            """)
        findings = lint(self.bundle)
        self.assertEqual(findings, [], msg="\n".join(str(f) for f in findings))


class TestPrototypeArtifacts(FixtureBase):
    """*.prototype/ directories hold throwaway prototype artifacts — never concepts."""

    def test_md_inside_prototype_dir_is_skipped(self) -> None:
        self.write_valid_root()
        self.write("payment-history-view.prototype/README.md",
                   "# How to run\n\nOpen index.html — no frontmatter, not a concept.\n")
        self.assertEqual(lint(self.bundle), [])

    def test_md_nested_deep_inside_prototype_dir_is_skipped(self) -> None:
        self.write_valid_root()
        self.write("billing/invoice-look.prototype/docs/notes.md",
                   "scaffolder output, no frontmatter\n")
        self.write("billing/map.md", """\
            ---
            type: Map
            generated: { by: claude-code/test-model, at: 2026-08-02T10:00:00Z }
            ---

            # Billing

            ## Destination

            Billing design resolved end to end.
            """)
        self.assertEqual(lint(self.bundle), [])

    def test_log_md_inside_prototype_dir_is_skipped(self) -> None:
        self.write_valid_root()
        self.write("payment-history-view.prototype/log.md",
                   "an artifact file that happens to be named log.md\n")
        self.assertEqual(lint(self.bundle), [])

    def test_index_md_inside_prototype_dir_is_skipped(self) -> None:
        self.write_valid_root()
        self.write("payment-history-view.prototype/index.md",
                   "artifact landing page, not the bundle pin\n")
        self.assertEqual(lint(self.bundle), [])

    def test_prototype_suffix_on_file_not_dir_is_still_linted(self) -> None:
        self.write_valid_root()
        self.write("stray.prototype.md", "# Stray\n\nNo frontmatter.\n")
        findings = lint(self.bundle)
        self.assertIn("missing-frontmatter", self.rules(findings))


class TestFrontmatterParsing(FixtureBase):
    def test_missing_frontmatter_is_error(self) -> None:
        self.write_valid_root()
        self.write("loose.md", "# Loose\n\nNo frontmatter at all.\n")
        findings = lint(self.bundle)
        self.assertIn("missing-frontmatter", self.rules(self.errors(findings)))

    def test_unterminated_frontmatter_is_error(self) -> None:
        self.write_valid_root()
        self.write("broken.md", "---\ntype: Decision\n\n# Broken\n")
        self.assertIn("unparseable-frontmatter", self.rules(self.errors(lint(self.bundle))))

    def test_missing_type_is_error(self) -> None:
        self.write_valid_root()
        self.write("untyped.md", "---\ntags: [x]\n---\n\n# Untyped\n\n## Question\n\nQ?\n")
        self.assertIn("missing-type", self.rules(self.errors(lint(self.bundle))))

    def test_unknown_type_is_error(self) -> None:
        self.write_valid_root()
        self.write("odd.md", "---\ntype: Playbook\n---\n\n# Odd\n\n## Question\n\nQ?\n")
        self.assertIn("unknown-type", self.rules(self.errors(lint(self.bundle))))

    def test_block_list_of_block_maps_parses(self) -> None:
        self.write_valid_root()
        self.write("r.md", """\
            ---
            type: Research
            generated: { by: waypoint-researcher/test-model, at: 2026-08-02T11:00:00Z }
            sources:
              - id: a
                resource: https://example.com/a
              - id: b
                resource: https://example.com/b
            ---

            # r

            ## Question

            Q?

            ## Findings

            Fact.[^a] Other fact.[^b]

            [^a]: A
            [^b]: B
            """)
        self.assertEqual(lint(self.bundle), [])


class TestIndexAndPin(FixtureBase):
    def test_missing_root_index_is_error(self) -> None:
        self.write("map.md", VALID_ROOT_MAP)
        self.assertIn("missing-index", self.rules(self.errors(lint(self.bundle))))

    def test_index_without_okf_version_is_error(self) -> None:
        self.write("map.md", VALID_ROOT_MAP)
        self.write("index.md", "# Design bundle\n\n* [Root map](map.md) - start here\n")
        self.assertIn("missing-okf-version", self.rules(self.errors(lint(self.bundle))))

    def test_wrong_okf_version_is_error(self) -> None:
        self.write("map.md", VALID_ROOT_MAP)
        self.write("index.md", '---\nokf_version: "0.3"\n---\n\n# D\n\n* [Root map](map.md) - start here\n')
        self.assertIn("wrong-okf-version", self.rules(self.errors(lint(self.bundle))))

    def test_index_with_extra_frontmatter_keys_is_error(self) -> None:
        self.write("map.md", VALID_ROOT_MAP)
        self.write("index.md", '---\nokf_version: "0.2"\ntype: Map\n---\n\n# D\n')
        self.assertIn("index-extra-keys", self.rules(self.errors(lint(self.bundle))))

    def test_non_root_index_with_frontmatter_is_error(self) -> None:
        self.write_valid_root()
        self.write("billing/index.md", '---\nokf_version: "0.2"\n---\n\n# Billing\n')
        self.assertIn("index-extra-keys", self.rules(self.errors(lint(self.bundle))))

    def test_log_file_is_error(self) -> None:
        self.write_valid_root()
        self.write("log.md", "# Log\n\n## 2026-08-09\n* **Update**: things.\n")
        self.assertIn("log-file", self.rules(self.errors(lint(self.bundle))))


class TestMaps(FixtureBase):
    def test_missing_root_map_is_error(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.assertIn("missing-root-map", self.rules(self.errors(lint(self.bundle))))

    def test_map_with_destination_only_is_valid(self) -> None:
        self.write_valid_root()
        self.write("billing/map.md", """\
            ---
            type: Map
            generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }
            ---

            # Billing

            ## Destination

            Billing resolved.
            """)
        self.assertEqual(lint(self.bundle), [])

    def test_map_without_destination_is_error(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("map.md", """\
            ---
            type: Map
            generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }
            ---

            # P

            ## Notes

            Operator actor id: human:tester
            """)
        self.assertIn("missing-destination", self.rules(self.errors(lint(self.bundle))))

    def test_unknown_map_section_is_error(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("map.md", VALID_ROOT_MAP + "\n## Session log\n\ncontent\n")
        self.assertIn("unknown-section", self.rules(self.errors(lint(self.bundle))))

    def test_empty_section_is_error(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("map.md", VALID_ROOT_MAP + "\n## Frontier\n")
        self.assertIn("empty-section", self.rules(self.errors(lint(self.bundle))))

    def test_map_not_named_map_md_is_error(self) -> None:
        self.write_valid_root()
        self.write("billing.md", """\
            ---
            type: Map
            generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }
            ---

            # Billing

            ## Destination

            Billing resolved.
            """)
        self.assertIn("map-filename", self.rules(self.errors(lint(self.bundle))))

    def test_map_md_without_map_type_is_error(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("map.md", VALID_ROOT_MAP.replace("type: Map", "type: Decision"))
        self.assertIn("map-filename", self.rules(self.errors(lint(self.bundle))))

    def test_annotated_region_entry_is_error(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("billing/map.md", """\
            ---
            type: Map
            generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }
            ---

            # Billing

            ## Destination

            Billing resolved.
            """)
        self.write("map.md", VALID_ROOT_MAP + textwrap.dedent("""\

            ## Regions

            - [billing](billing/map.md) — mostly done
            """))
        self.assertIn("annotated-entry", self.rules(self.errors(lint(self.bundle))))

    def test_decisions_entry_without_gist_is_error(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("done.md", """\
            ---
            type: Decision
            generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }
            verified: { by: human:tester, at: 2026-08-09T10:05:00Z }
            ---

            # done

            ## Question

            Q?

            ## Decision

            A, because B.
            """)
        self.write("map.md", VALID_ROOT_MAP + textwrap.dedent("""\

            ## Decisions so far

            - [done](done.md)
            """))
        self.assertIn("missing-annotation", self.rules(self.errors(lint(self.bundle))))

    def test_broken_state_link_is_error(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("map.md", VALID_ROOT_MAP + textwrap.dedent("""\

            ## Frontier

            - [ghost](ghost.md)
            """))
        self.assertIn("broken-link", self.rules(self.errors(lint(self.bundle))))

    def test_broken_body_link_elsewhere_is_warning(self) -> None:
        self.write_valid_root()
        self.write("w.md", """\
            ---
            type: Decision
            generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }
            ---

            # w

            ## Question

            Relates to [ghost](ghost.md)?
            """)
        findings = lint(self.bundle)
        self.assertIn("broken-link", self.rules(self.warnings(findings)))
        self.assertNotIn("broken-link", self.rules(self.errors(findings)))

    def test_external_links_are_ignored(self) -> None:
        self.write("index.md", VALID_INDEX)
        self.write("map.md", VALID_ROOT_MAP + textwrap.dedent("""\

            ## Issues cut

            1. [#12](https://forgejo.example/o/r/issues/12) — first slice
            """))
        self.assertEqual(lint(self.bundle), [])


class TestWaypoints(FixtureBase):
    def waypoint(self, body: str, frontmatter: str = "type: Decision\ngenerated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }") -> None:
        self.write("w.md", f"---\n{frontmatter}\n---\n\n# w\n\n{textwrap.dedent(body)}")

    def test_status_key_is_error(self) -> None:
        self.write_valid_root()
        self.waypoint("## Question\n\nQ?\n",
                      "type: Decision\nstatus: draft\ngenerated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }")
        self.assertIn("status-key", self.rules(self.errors(lint(self.bundle))))

    def test_missing_question_is_error(self) -> None:
        self.write_valid_root()
        self.waypoint("Some prose.\n")
        self.assertIn("missing-question", self.rules(self.errors(lint(self.bundle))))

    def test_filled_decision_without_human_verifier_is_error(self) -> None:
        self.write_valid_root()
        self.waypoint("## Question\n\nQ?\n\n## Decision\n\nA, because B.\n")
        self.assertIn("smuggled-resolution", self.rules(self.errors(lint(self.bundle))))

    def test_machine_verifier_alone_is_still_smuggled(self) -> None:
        self.write_valid_root()
        self.waypoint(
            "## Question\n\nQ?\n\n## Decision\n\nA, because B.\n",
            "type: Decision\n"
            "generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }\n"
            "verified: { by: process:nightly, at: 2026-08-09T10:05:00Z }")
        self.assertIn("smuggled-resolution", self.rules(self.errors(lint(self.bundle))))

    def test_verified_list_with_human_passes(self) -> None:
        self.write_valid_root()
        self.waypoint(
            "## Question\n\nQ?\n\n## Decision\n\nA, because B.\n",
            "type: Decision\n"
            "generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }\n"
            "verified:\n"
            "  - { by: process:nightly, at: 2026-08-09T10:05:00Z }\n"
            "  - { by: human:tester, at: 2026-08-09T10:06:00Z }")
        self.assertEqual(lint(self.bundle), [])

    def test_verified_missing_at_is_error(self) -> None:
        self.write_valid_root()
        self.waypoint(
            "## Question\n\nQ?\n\n## Decision\n\nA, because B.\n",
            "type: Decision\n"
            "generated: { by: claude-code/test-model, at: 2026-08-09T10:00:00Z }\n"
            "verified: { by: human:tester }")
        self.assertIn("malformed-verified", self.rules(self.errors(lint(self.bundle))))

    def test_generated_missing_by_is_error(self) -> None:
        self.write_valid_root()
        self.waypoint("## Question\n\nQ?\n",
                      "type: Decision\ngenerated: { at: 2026-08-09T10:00:00Z }")
        self.assertIn("malformed-generated", self.rules(self.errors(lint(self.bundle))))

    def test_missing_generated_is_warning(self) -> None:
        self.write_valid_root()
        self.waypoint("## Question\n\nQ?\n", "type: Decision")
        findings = lint(self.bundle)
        self.assertIn("missing-generated", self.rules(self.warnings(findings)))
        self.assertEqual(self.errors(findings), [])


class TestResearch(FixtureBase):
    def test_findings_without_sources_is_error(self) -> None:
        self.write_valid_root()
        self.write("r.md", """\
            ---
            type: Research
            generated: { by: waypoint-researcher/test-model, at: 2026-08-09T10:00:00Z }
            ---

            # r

            ## Question

            Q?

            ## Findings

            A bare, uncited claim.
            """)
        self.assertIn("findings-without-sources", self.rules(self.errors(lint(self.bundle))))

    def test_footnote_without_matching_source_id_is_error(self) -> None:
        self.write_valid_root()
        self.write("r.md", """\
            ---
            type: Research
            generated: { by: waypoint-researcher/test-model, at: 2026-08-09T10:00:00Z }
            sources:
              - id: real
                resource: https://example.com/real
            ---

            # r

            ## Question

            Q?

            ## Findings

            Cited claim.[^real] Phantom claim.[^phantom]

            [^real]: Real
            [^phantom]: Phantom
            """)
        self.assertIn("unmatched-footnote", self.rules(self.errors(lint(self.bundle))))

    def test_source_without_resource_is_error(self) -> None:
        self.write_valid_root()
        self.write("r.md", """\
            ---
            type: Research
            generated: { by: waypoint-researcher/test-model, at: 2026-08-09T10:00:00Z }
            sources:
              - id: nores
                title: A source with no resource
            ---

            # r

            ## Question

            Q?

            ## Findings

            Claim.[^nores]

            [^nores]: A source with no resource
            """)
        self.assertIn("source-missing-resource", self.rules(self.errors(lint(self.bundle))))


VALID_DOCS_INDEX = """\
---
okf_version: "0.2"
---

# Docs bundle

* [Storage module](storage.md) - the storage layer
"""

VALID_DOCS_MODULE = """\
---
type: Module
title: Storage
generated: { by: claude-code/test-model, at: 2026-08-16T10:00:00Z }
code_commit: abc1234
sources:
  - { id: src, resource: ../src/storage.py }
---

# Surface

`save()` and `load()`.
"""

VALID_HUMAN_GUIDE = """\
---
type: Guide
title: Operating notes
generated: { by: human:tester, at: 2026-08-16T10:00:00Z }
---

# Notes

Hand-authored operating advice.
"""


class DocsFixtureBase(FixtureBase):
    # These fixtures write no files outside docs/, so the symbol-existence
    # corpus is empty and that check stands down. A test that adds any
    # non-prose file under self.root brings the check to life — VALID_DOCS_MODULE
    # mentions `save()` and `load()`, which would then need to exist.
    def setUp(self) -> None:
        super().setUp()
        self.bundle = self.root / "docs"
        self.bundle.mkdir()

    def write_valid_docs_root(self) -> None:
        self.write("index.md", VALID_DOCS_INDEX)


class TestDocsMode(DocsFixtureBase):
    def test_minimal_docs_bundle_is_clean(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE)
        self.assertEqual(lint(self.bundle, kind="docs"), [])

    def test_no_root_map_required(self) -> None:
        self.write_valid_docs_root()
        findings = lint(self.bundle, kind="docs")
        self.assertNotIn("missing-root-map", self.rules(findings))

    def test_all_six_machine_types_accepted(self) -> None:
        self.write_valid_docs_root()
        for i, ctype in enumerate(["Module", "Helper", "CLI", "Playbook", "DataModel", "API"]):
            self.write(f"c{i}.md", VALID_DOCS_MODULE.replace("type: Module", f"type: {ctype}"))
        self.assertEqual(lint(self.bundle, kind="docs"), [])

    def test_design_type_is_unknown_in_docs_mode(self) -> None:
        self.write_valid_docs_root()
        self.write("waypoint.md", VALID_DOCS_MODULE.replace("type: Module", "type: Research"))
        findings = lint(self.bundle, kind="docs")
        self.assertIn("unknown-type", self.rules(self.errors(findings)))

    def test_human_authored_concept_may_carry_any_type(self) -> None:
        self.write_valid_docs_root()
        self.write("guide.md", VALID_HUMAN_GUIDE)
        self.assertEqual(lint(self.bundle, kind="docs"), [])

    def test_machine_concept_with_nonstandard_type_is_error(self) -> None:
        self.write_valid_docs_root()
        self.write("guide.md", VALID_HUMAN_GUIDE.replace("human:tester", "claude-code/test-model"))
        findings = lint(self.bundle, kind="docs")
        self.assertIn("unknown-type", self.rules(self.errors(findings)))

    def test_missing_generated_is_error_in_docs_mode(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE.replace(
            "generated: { by: claude-code/test-model, at: 2026-08-16T10:00:00Z }\n", ""))
        findings = lint(self.bundle, kind="docs")
        self.assertIn("missing-generated", self.rules(self.errors(findings)))

    def test_machine_concept_without_sources_is_error(self) -> None:
        self.write_valid_docs_root()
        content = VALID_DOCS_MODULE.replace(
            "sources:\n  - { id: src, resource: ../src/storage.py }\n", "")
        self.write("storage.md", content)
        findings = lint(self.bundle, kind="docs")
        self.assertIn("machine-concept-without-sources", self.rules(self.errors(findings)))

    def test_human_concept_without_sources_is_fine(self) -> None:
        self.write_valid_docs_root()
        self.write("guide.md", VALID_HUMAN_GUIDE)
        findings = lint(self.bundle, kind="docs")
        self.assertNotIn("machine-concept-without-sources", self.rules(findings))

    def test_status_value_validated(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE.replace(
            "type: Module", "type: Module\nstatus: golden"))
        findings = lint(self.bundle, kind="docs")
        self.assertIn("invalid-status", self.rules(self.errors(findings)))

    def test_lifecycle_status_values_accepted(self) -> None:
        self.write_valid_docs_root()
        for i, status in enumerate(["draft", "stable", "deprecated"]):
            self.write(f"c{i}.md", VALID_DOCS_MODULE.replace(
                "type: Module", f"type: Module\nstatus: {status}"))
        self.assertEqual(lint(self.bundle, kind="docs"), [])

    def test_stale_after_must_be_iso_date(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE.replace(
            "type: Module", "type: Module\nstale_after: soon"))
        findings = lint(self.bundle, kind="docs")
        self.assertIn("invalid-stale-after", self.rules(self.errors(findings)))

    def test_stale_after_iso_date_accepted(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE.replace(
            "type: Module", "type: Module\nstale_after: 2026-12-31"))
        self.assertEqual(lint(self.bundle, kind="docs"), [])

    def test_log_md_is_allowed_with_date_headings(self) -> None:
        self.write_valid_docs_root()
        self.write("log.md", "# Update log\n\n## 2026-08-16\n* **Creation**: founded.\n")
        self.assertEqual(lint(self.bundle, kind="docs"), [])

    def test_log_md_non_date_heading_is_error(self) -> None:
        self.write_valid_docs_root()
        self.write("log.md", "# Update log\n\n## Recent changes\n* stuff.\n")
        findings = lint(self.bundle, kind="docs")
        self.assertIn("log-heading-not-date", self.rules(self.errors(findings)))

    def test_log_md_with_frontmatter_is_error(self) -> None:
        self.write_valid_docs_root()
        self.write("log.md", "---\ntype: Log\n---\n\n## 2026-08-16\n* founded.\n")
        findings = lint(self.bundle, kind="docs")
        self.assertIn("log-frontmatter", self.rules(self.errors(findings)))

    def test_broken_body_link_is_warning_in_docs_mode(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE + "\nSee [gone](missing.md).\n")
        findings = lint(self.bundle, kind="docs")
        self.assertIn("broken-link", self.rules(self.warnings(findings)))
        self.assertEqual(self.errors(findings), [])

    def test_status_key_allowed_in_docs_mode(self) -> None:
        # design mode bans OKF status; docs mode uses it as lifecycle
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE.replace(
            "type: Module", "type: Module\nstatus: draft"))
        findings = lint(self.bundle, kind="docs")
        self.assertNotIn("status-key", self.rules(findings))

    def test_footnote_without_matching_source_id_is_error(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE + "\nClaim.[^nope]\n\n[^nope]: gone\n")
        findings = lint(self.bundle, kind="docs")
        self.assertIn("unmatched-footnote", self.rules(self.errors(findings)))

    def test_regex_class_in_inline_code_is_not_a_footnote(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE +
                   "\nFilenames are sanitized with `re.sub(r\"[^\\w\\-]\", \"_\", name)`.\n")
        findings = lint(self.bundle, kind="docs")
        self.assertNotIn("unmatched-footnote", self.rules(findings))

    def test_regex_class_in_fenced_code_is_not_a_footnote(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE +
                   "\n```python\npattern = r\"[^abc]\"\n```\n")
        findings = lint(self.bundle, kind="docs")
        self.assertNotIn("unmatched-footnote", self.rules(findings))

    def test_design_mode_remains_default(self) -> None:
        # the design bundle from the existing fixtures still lints clean with no kind arg
        self.bundle = self.root / "design"  # already created by FixtureBase.setUp
        self.write_valid_root()
        self.assertEqual(lint(self.bundle), [])


DAEMON_SRC = """\
class Daemon:
    retries = 3

    def __init__(self):
        self.channel = None

    def startup(self):
        return self._boot()

    def _boot(self):
        return True


def deliver():
    return asyncio.gather()
"""

DOCS_DAEMON_HEADER = """\
---
type: Module
title: Daemon
generated: { by: claude-code/test-model, at: 2026-08-16T10:00:00Z }
code_commit: abc1234
sources:
  - { id: src, resource: ../src/daemon.py }
---

# Daemon

"""


class SymbolFixtureBase(DocsFixtureBase):
    def setUp(self) -> None:
        super().setUp()
        self.write_valid_docs_root()

    def write_src(self, rel: str = "src/daemon.py", content: str = DAEMON_SRC) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def write_concept(self, body: str, header: str = DOCS_DAEMON_HEADER) -> Path:
        return self.write("daemon.md", header + body)

    def docs_findings(self):
        return lint(self.bundle, kind="docs")


class TestSymbolExistence(SymbolFixtureBase):
    def test_fabricated_method_on_repo_class_is_error(self) -> None:
        # `start` appears in source prose, but Daemon defines no start member —
        # class membership must catch what a bare text search would pass.
        self.write_src(content=DAEMON_SRC + "\n# how to start the daemon\n")
        self.write_concept("Boot with `Daemon.start()`.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_existing_method_via_class_membership_passes(self) -> None:
        self.write_src()
        self.write_concept("Boot with `Daemon.startup()`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_class_attribute_and_instance_attribute_pass(self) -> None:
        self.write_src()
        self.write_concept("Tune `Daemon.retries`; the sink is `Daemon.channel`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_deep_dotted_path_checks_the_immediate_member_only(self) -> None:
        # `Daemon.channel.maxLength`: only `channel` is statically checkable
        # against Daemon — what its value carries is beyond the indexer's reach.
        self.write_src()
        self.write_concept("Schema pins `Daemon.channel.maxLength`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_deep_dotted_path_with_missing_immediate_member_is_error(self) -> None:
        self.write_src()
        self.write_concept("Schema pins `Daemon.mailbox.maxLength`.\n")
        findings = self.docs_findings()
        errors = self.errors(findings)
        self.assertIn("unknown-symbol", self.rules(errors))
        self.assertIn("`mailbox`", errors[0].message)

    def test_fabricated_private_helper_is_error(self) -> None:
        self.write_src()
        self.write_concept("Handlers come from `_build_handler_services`.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_bare_call_missing_is_error(self) -> None:
        self.write_src()
        self.write_concept("Then `frobnicate()` runs.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_external_dotted_reference_passes_by_text(self) -> None:
        # asyncio is not a repo class; the terminal name appears in source text.
        self.write_src()
        self.write_concept("Fan-in uses `asyncio.gather`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_symbol_only_in_markdown_does_not_count(self) -> None:
        # The Chantry fabrication originated in a CLAUDE.md: docs are claims,
        # not definitions, so markdown never counts as source.
        self.write_src()
        (self.root / "CLAUDE.md").write_text("Boot with `Daemon.start()`.\n")
        self.write_concept("Boot with `Daemon.start()`.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_symbol_in_fenced_code_block_not_checked(self) -> None:
        # The fenced content must itself carry an inline-backticked span —
        # a bare `Daemon.start()` line would pass even without fence handling.
        self.write_src()
        self.write_concept("```markdown\nBoot with `Daemon.start()`.\n```\n")
        self.assertEqual(self.docs_findings(), [])

    def test_symbol_in_nested_fence_not_checked(self) -> None:
        # A four-backtick fence wrapping a three-backtick example: the inner
        # run must not close the outer fence.
        self.write_src()
        self.write_concept(
            "````markdown\n```\nBoot with `Daemon.start()`.\n```\n````\n")
        self.assertEqual(self.docs_findings(), [])

    def test_symbol_in_tilde_fence_not_checked(self) -> None:
        self.write_src()
        self.write_concept("~~~\nBoot with `Daemon.start()`.\n~~~\n")
        self.assertEqual(self.docs_findings(), [])

    def test_inherited_member_passes(self) -> None:
        self.write_src(content=DAEMON_SRC + "\nclass Worker(Daemon):\n    pass\n")
        self.write_concept("Boot with `Worker.startup()`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_unresolvable_base_falls_back_to_text(self) -> None:
        # Client inherits from an external SDK class: the index cannot claim
        # authority over its members, so the text corpus decides.
        self.write_src(content=DAEMON_SRC
                       + "\nclass Client(RemoteBase):\n    pass\n# send a request\n")
        self.write_concept("Call `Client.request()`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_unresolvable_base_with_no_text_match_is_error(self) -> None:
        self.write_src(content=DAEMON_SRC + "\nclass Client(RemoteBase):\n    pass\n")
        self.write_concept("Call `Client.zz_nowhere()`.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_uppercase_markdown_is_not_source(self) -> None:
        self.write_src()
        (self.root / "CLAUDE.MD").write_text("Uses `_special_helper` heavily.\n")
        self.write_concept("Handled by `_special_helper`.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_rst_is_not_source(self) -> None:
        self.write_src()
        (self.root / "docs-old.rst").write_text("Uses `_special_helper` heavily.\n")
        self.write_concept("Handled by `_special_helper`.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_empty_source_file_still_enables_check(self) -> None:
        # Stand-down keys on "no source files", not "no source bytes".
        self.write_src(content="")
        self.write_concept("Then `frobnicate()` runs.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_waiver_reason_after_plain_hyphen_is_not_waived(self) -> None:
        # Token collection stops at the first non-symbol-shaped word, so a
        # reason clause cannot silently waive symbols it happens to mention.
        self.write_src()
        self.write_concept(
            "Emits `_complete`; then `frobnicate()` runs.\n\n"
            "<!-- symbols-ok: _complete - real entry is frobnicate() -->\n")
        findings = self.docs_findings()
        errors = self.errors(findings)
        self.assertIn("unknown-symbol", self.rules(errors))
        self.assertIn("frobnicate", errors[0].message)

    def test_null_byte_python_file_does_not_crash(self) -> None:
        self.write_src()
        self.write_src(rel="src/bad.py", content="x = 1\n\x00")
        self.write_concept("Boot with `Daemon.startup()`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_oversized_file_is_not_corpus(self) -> None:
        self.write_src()
        self.write_src(rel="src/huge.py",
                       content="def frobnicate(): pass\n# " + "x" * 1_100_000 + "\n")
        self.write_concept("Then `frobnicate()` runs.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_unreadable_source_file_is_warned_about(self) -> None:
        self.write_src()
        secret = self.root / "src" / "secret.py"
        secret.write_text("def frobnicate(): pass\n")
        secret.chmod(0)
        self.addCleanup(secret.chmod, 0o644)
        try:
            secret.read_text()
        except PermissionError:
            pass
        else:
            self.skipTest("running with permissions that ignore chmod 0")
        self.write_concept("Boot with `Daemon.startup()`.\n")
        findings = self.docs_findings()
        self.assertIn("unreadable-source", self.rules(self.warnings(findings)))

    def test_root_dotfile_is_not_corpus(self) -> None:
        self.write_src()
        (self.root / ".envrc").write_text("frobnicate\n")
        self.write_concept("Then `frobnicate()` runs.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_symlinked_file_is_not_corpus(self) -> None:
        self.write_src()
        outside = self.root.parent / f"{self.root.name}-linked-source"
        outside.write_text("def frobnicate(): pass\n")
        self.addCleanup(outside.unlink, missing_ok=True)
        extra = self.root / "extra"
        extra.mkdir()
        (extra / "linked.py").symlink_to(outside)
        self.write_concept("Then `frobnicate()` runs.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.errors(findings)))

    def test_foreign_extension_filename_not_a_symbol(self) -> None:
        self.write_src()
        self.write_concept("The parser lives in `handler.rb`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_filename_in_backticks_not_a_symbol(self) -> None:
        self.write_src()
        self.write_concept("Config lives in `missing.toml`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_hostname_not_a_symbol(self) -> None:
        self.write_src()
        self.write_concept("Blocks `metadata.google.internal` and `good.com.evil.net`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_waived_symbol_is_skipped(self) -> None:
        self.write_src()
        self.write_concept(
            "Emits `_complete` events.\n\n"
            "<!-- symbols-ok: _complete — table shorthand for log_working_* -->\n")
        self.assertEqual(self.docs_findings(), [])

    def test_waiver_covers_only_listed_symbols(self) -> None:
        self.write_src()
        self.write_concept(
            "Emits `_complete` then `_finish`.\n\n"
            "<!-- symbols-ok: _complete -->\n")
        findings = self.docs_findings()
        errors = self.errors(findings)
        self.assertIn("unknown-symbol", self.rules(errors))
        self.assertIn("_finish", errors[0].message)
        self.assertNotIn("_complete", errors[0].message)

    def test_missing_symbol_in_human_concept_is_warning(self) -> None:
        self.write_src()
        self.write("threat.md",
                   VALID_HUMAN_GUIDE + "\nScans via `hardening.check_secret_handling`.\n")
        findings = self.docs_findings()
        self.assertIn("unknown-symbol", self.rules(self.warnings(findings)))
        self.assertEqual(self.errors(findings), [])

    def test_no_source_corpus_skips_check(self) -> None:
        # A bundle with nothing outside it to check against: the check stands down.
        self.write_concept("Boot with `Daemon.start()`.\n")
        self.assertNotIn("unknown-symbol", self.rules(self.docs_findings()))

    def test_log_md_is_not_scanned_for_symbols(self) -> None:
        self.write_src()
        self.write("log.md",
                   "# Update log\n\n## 2026-08-16\n* Fixed fabricated `Daemon.start()`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_symlink_escaping_the_repo_does_not_crash(self) -> None:
        # .git/hooks/pre-commit is routinely a symlink to a file outside the
        # repo; the corpus walk must classify by the unresolved path.
        self.write_src()
        outside = self.root.parent / f"{self.root.name}-outside-target"
        outside.write_text("#!/bin/sh\n")
        self.addCleanup(outside.unlink, missing_ok=True)
        hooks = self.root / ".git" / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "pre-commit").symlink_to(outside)
        self.write_concept("Boot with `Daemon.startup()`.\n")
        self.assertEqual(self.docs_findings(), [])

    def test_design_kind_has_no_symbol_check(self) -> None:
        # Design bundles document intent; their symbols may rightly not exist yet.
        self.bundle = self.root / "design"
        self.write_valid_root()
        self.write_src()
        self.write("idea.md", """\
            ---
            type: Research
            generated: { by: claude-code/test-model, at: 2026-08-01T10:00:00Z }
            ---

            # idea

            ## Question

            Should `Daemon.start()` exist?
            """)
        self.assertNotIn("unknown-symbol", self.rules(lint(self.bundle)))


class TestLinksInCode(SymbolFixtureBase):
    def test_link_in_fenced_code_is_not_checked_docs(self) -> None:
        self.write_concept("```markdown\n![chart](chart.png)\n```\n")
        self.assertNotIn("broken-link", self.rules(self.docs_findings()))

    def test_link_in_inline_code_is_not_checked_docs(self) -> None:
        self.write_concept("Render with `![chart](chart.png)` syntax.\n")
        self.assertNotIn("broken-link", self.rules(self.docs_findings()))

    def test_broken_link_after_fence_keeps_its_line_number(self) -> None:
        body = "```\nfence\n```\n\nSee [gone](missing.md).\n"
        path = self.write_concept(body)
        expected_line = path.read_text().splitlines().index("See [gone](missing.md).") + 1
        findings = [f for f in self.docs_findings() if f.rule == "broken-link"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line, expected_line)

    def test_link_in_fenced_code_is_not_checked_design(self) -> None:
        self.bundle = self.root / "design"
        self.write_valid_root()
        self.write("idea.md", """\
            ---
            type: Research
            generated: { by: claude-code/test-model, at: 2026-08-01T10:00:00Z }
            ---

            # idea

            ## Question

            Example output:

            ```markdown
            ![chart](chart.png)
            ```
            """)
        self.assertNotIn("broken-link", self.rules(lint(self.bundle)))


class TestDocsCli(DocsFixtureBase):
    SCRIPT = Path(__file__).parent / "lint_bundle.py"

    def test_kind_flag(self) -> None:
        self.write_valid_docs_root()
        self.write("storage.md", VALID_DOCS_MODULE)
        clean = subprocess.run(
            [sys.executable, str(self.SCRIPT), "--kind", "docs", str(self.bundle)],
            capture_output=True, text=True)
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)

        bad_kind = subprocess.run(
            [sys.executable, str(self.SCRIPT), "--kind", "wiki", str(self.bundle)],
            capture_output=True, text=True)
        self.assertEqual(bad_kind.returncode, 2)


class TestCli(FixtureBase):
    SCRIPT = Path(__file__).parent / "lint_bundle.py"

    def test_exit_codes(self) -> None:
        self.write_valid_root()
        clean = subprocess.run([sys.executable, str(self.SCRIPT), str(self.bundle)],
                               capture_output=True, text=True)
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)

        self.write("loose.md", "# no frontmatter\n")
        dirty = subprocess.run([sys.executable, str(self.SCRIPT), str(self.bundle)],
                               capture_output=True, text=True)
        self.assertEqual(dirty.returncode, 1)
        self.assertIn("missing-frontmatter", dirty.stdout)

        usage = subprocess.run([sys.executable, str(self.SCRIPT)],
                               capture_output=True, text=True)
        self.assertEqual(usage.returncode, 2)


if __name__ == "__main__":
    unittest.main()
