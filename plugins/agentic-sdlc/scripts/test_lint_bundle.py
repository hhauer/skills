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
