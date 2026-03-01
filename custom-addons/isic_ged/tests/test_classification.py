from odoo.exceptions import ValidationError

from .common import IsicGedCase


class TestClassification(IsicGedCase):
    """Tests for automatic document classification."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Deactivate all existing classification rules (from XML data)
        cls.env["isic.document.classification.rule"].search([]).write({"active": False})
        # Create classification rules for tests
        cls.rule_pv = cls.env["isic.document.classification.rule"].create(
            {
                "name": "PV Rule",
                "sequence": 1,
                "match_type": "filename",
                "match_pattern": "PV_*",
                "document_type_id": cls.doc_type_with_validation.id,
            }
        )
        cls.rule_ext = cls.env["isic.document.classification.rule"].create(
            {
                "name": "TXT Rule",
                "sequence": 10,
                "match_type": "extension",
                "match_pattern": "txt",
                "document_type_id": cls.doc_type_without_validation.id,
            }
        )

    def test_auto_classify_on_create(self):
        """New file matching a rule should be auto-classified."""
        f = self._create_file(name="PV_Conseil_2025.pdf")

        self.assertTrue(f.auto_classified)
        self.assertEqual(f.document_type_id, self.doc_type_with_validation)

    def test_auto_classify_by_extension(self):
        """File matching extension rule should be classified."""
        f = self._create_file(name="notes.txt")

        self.assertTrue(f.auto_classified)
        self.assertEqual(f.document_type_id, self.doc_type_without_validation)

    def test_no_match_no_classification(self):
        """File not matching any rule should not be classified."""
        f = self._create_file(name="random_document.docx")

        self.assertFalse(f.auto_classified)
        self.assertFalse(f.document_type_id)

    def test_manual_classification_preserved(self):
        """Manually classified files should not be overwritten by auto-classification."""
        f = self._create_file(
            name="PV_meeting.pdf",
            document_type_id=self.doc_type_without_validation.id,
        )

        # Should keep the manual classification (doc_type_without_validation)
        # because it was set manually (auto_classified=False initially)
        self.assertEqual(f.document_type_id, self.doc_type_without_validation)

    def test_rename_triggers_reclassification(self):
        """Renaming a file should trigger auto-classification if auto-classified."""
        f = self._create_file(name="random.pdf")
        self.assertFalse(f.auto_classified)

        # Rename to match a rule
        f.write({"name": "PV_nouveau.pdf"})
        self.assertTrue(f.auto_classified)
        self.assertEqual(f.document_type_id, self.doc_type_with_validation)

    def test_rule_priority(self):
        """First matching rule (by sequence) should win."""
        # Create a conflicting rule with higher sequence (lower priority)
        self.env["isic.document.classification.rule"].create(
            {
                "name": "PV Low Priority",
                "sequence": 99,
                "match_type": "filename",
                "match_pattern": "PV_*",
                "document_type_id": self.doc_type_without_validation.id,
            }
        )

        f = self._create_file(name="PV_test.pdf")
        # Should match rule_pv (sequence=1) not the new rule (sequence=99)
        self.assertEqual(f.document_type_id, self.doc_type_with_validation)

    def test_case_insensitive_match(self):
        """Rules should match case-insensitively by default."""
        f = self._create_file(name="pv_lowercase.pdf")
        self.assertTrue(f.auto_classified)

    def test_empty_pattern_rejected(self):
        """Rule with empty pattern should be rejected."""
        with self.assertRaises(ValidationError):
            self.env["isic.document.classification.rule"].create(
                {
                    "name": "Bad Rule",
                    "match_type": "filename",
                    "match_pattern": "   ",
                }
            )

    def test_rule_with_tags(self):
        """Rule with tags should add them to the file."""
        tag = self.env["dms.tag"].create({"name": "Auto-Tag"})
        self.rule_pv.write({"tag_ids": [(4, tag.id)]})

        f = self._create_file(name="PV_with_tags.pdf")
        self.assertIn(tag, f.tag_ids)

    def test_directory_match(self):
        """Directory-based classification should work."""
        self.env["isic.document.classification.rule"].create(
            {
                "name": "Direction Rule",
                "sequence": 5,
                "match_type": "directory",
                "match_pattern": "Direction",
                "document_type_id": self.doc_type_with_validation.id,
            }
        )
        # Create a subdirectory under root
        sub_dir = self.env["dms.directory"].create(
            {
                "name": "Direction",
                "parent_id": self.directory.id,
                "storage_id": self.storage.id,
            }
        )
        f = self._create_file(name="memo.pdf", directory_id=sub_dir.id)
        self.assertTrue(f.auto_classified)
