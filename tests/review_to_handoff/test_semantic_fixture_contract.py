from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from scripts import verify_repo

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = (ROOT / "docs" / "governance" / "REVIEW_PROTOCOL.md").resolve()
ADVISORY_HEADING = "## پرامپت اقدام"
ALTERNATE_HEADING = "## اقدام پیشنهادی"


class ReviewToHandoffAdvisoryHeadingTests(TestCase):
    def _contract_errors_for_protocol(self, protocol_text: str) -> list[str]:
        original_read_text = Path.read_text

        def read_text(path: Path, *args, **kwargs):
            if path.resolve() == PROTOCOL_PATH:
                return protocol_text
            return original_read_text(path, *args, **kwargs)

        errors: list[str] = []
        with patch.object(Path, "read_text", new=read_text):
            verify_repo.check_review_to_handoff_contract(errors)
        return errors

    def test_preferred_action_heading_is_not_a_required_exact_marker(self):
        self.assertNotIn(ADVISORY_HEADING, verify_repo.REVIEW_TO_HANDOFF_PROTOCOL_MARKERS)

    def test_changing_only_preferred_action_heading_preserves_contract(self):
        protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
        changed = protocol.replace(ADVISORY_HEADING, ALTERNATE_HEADING)
        self.assertNotEqual(changed, protocol)
        self.assertEqual(self._contract_errors_for_protocol(changed), [])

    def test_decision_material_handoff_markers_still_fail_closed(self):
        protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
        mandatory_markers = (
            "A prompt-required delegated route is an incomplete handoff",
            "When `BOUNDED` is selected for a material repair",
            "Do not derive merge-blocking mechanically from finding severity",
            "version-/runtime-bounded",
            "three logically distinct surfaces",
            "[IMPLEMENTATION CONTRACT]",
            "[VALIDATION CONTRACT]",
            "[POST-IMPLEMENTATION REPORT]",
        )

        for marker in mandatory_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, verify_repo.REVIEW_TO_HANDOFF_PROTOCOL_MARKERS)
                mutated = protocol.replace(marker, "REMOVED_DECISION_MATERIAL_MARKER")
                self.assertNotEqual(mutated, protocol)
                errors = self._contract_errors_for_protocol(mutated)
                self.assertTrue(
                    any(f"review-to-handoff protocol marker missing: {marker}" == error for error in errors),
                    errors,
                )
