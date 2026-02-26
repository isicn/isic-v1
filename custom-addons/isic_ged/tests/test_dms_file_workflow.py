from odoo.exceptions import UserError
from odoo.tests import Form

from .common import IsicGedCase


class TestDmsFileWorkflow(IsicGedCase):
    """Tests for dms.file GED workflow (state machine)."""

    def _make_direction_user(self, login):
        """Create a direction user with DMS access."""
        user = self.env["res.users"].create(
            {
                "name": f"Director {login}",
                "login": login,
                "group_ids": [(4, self.env.ref("isic_base.group_isic_direction").id)],
            }
        )
        self.access_group.write({"explicit_user_ids": [(4, user.id)]})
        # Flush so DMS raw SQL queries see the user in dms_access_group_users_rel
        self.env.flush_all()
        return user

    # ---- Validate ----

    def test_validate_draft_to_validated(self):
        """draft -> validated transition works."""
        f = self._create_file()
        self.assertEqual(f.ged_state, "draft")
        f.action_validate()
        self.assertEqual(f.ged_state, "validated")

    def test_validate_non_draft_raises(self):
        """Validating a non-draft file raises UserError."""
        f = self._create_file()
        f.action_validate()
        with self.assertRaises(UserError):
            f.action_validate()  # already validated

    def test_validate_sets_user_and_date(self):
        """action_validate sets valideur_id and date_validation."""
        f = self._create_file()
        f.action_validate()
        self.assertEqual(f.valideur_id.id, self.env.uid)
        self.assertTrue(f.date_validation)

    # ---- Archive ----

    def test_archive_validated_ok(self):
        """validated -> archived works."""
        f = self._create_file(document_type_id=self.doc_type_with_validation.id)
        f.action_validate()
        f.action_archive_ged()
        self.assertEqual(f.ged_state, "archived")

    def test_archive_requires_validation_when_type_requires(self):
        """Type with validation_required: archiving draft raises UserError."""
        f = self._create_file(document_type_id=self.doc_type_with_validation.id)
        with self.assertRaises(UserError):
            f.action_archive_ged()

    def test_archive_no_validation_required_ok(self):
        """Type without validation_required: draft -> archived directly."""
        f = self._create_file(document_type_id=self.doc_type_without_validation.id)
        f.action_archive_ged()
        self.assertEqual(f.ged_state, "archived")

    # ---- Reset to draft ----

    def test_reset_draft_direction_only(self):
        """Non-direction user cannot reset to draft."""
        basic_user = self.env["res.users"].create(
            {
                "name": "Basic GED User",
                "login": "basic_ged_user",
                "group_ids": [(4, self.env.ref("base.group_user").id)],
            }
        )
        self.access_group.write({"explicit_user_ids": [(4, basic_user.id)]})
        self.env.flush_all()
        f = self._create_file()
        f.action_validate()
        with self.assertRaises(UserError):
            f.with_user(basic_user).action_reset_draft()

    def test_reset_draft_clears_validation(self):
        """Reset to draft clears valideur_id and date_validation."""
        direction_user = self._make_direction_user("dir_ged_user")
        f = self._create_file()
        f.action_validate()
        self.assertTrue(f.valideur_id)
        self.assertTrue(f.date_validation)
        f.with_user(direction_user).action_reset_draft()
        self.assertEqual(f.ged_state, "draft")
        self.assertFalse(f.valideur_id)
        self.assertFalse(f.date_validation)

    def test_reset_draft_from_archived(self):
        """archived -> draft for direction user."""
        direction_user = self._make_direction_user("dir_ged_user2")
        f = self._create_file(document_type_id=self.doc_type_without_validation.id)
        f.action_archive_ged()
        self.assertEqual(f.ged_state, "archived")
        f.with_user(direction_user).action_reset_draft()
        self.assertEqual(f.ged_state, "draft")

    def test_reset_draft_from_validated(self):
        """validated -> draft for direction user."""
        direction_user = self._make_direction_user("dir_ged_user3")
        f = self._create_file()
        f.action_validate()
        f.with_user(direction_user).action_reset_draft()
        self.assertEqual(f.ged_state, "draft")

    # ---- Onchange & fields ----

    def test_onchange_document_type_populates_year(self):
        """Setting document_type auto-fills annee_academique from current year."""
        f = self._create_file()
        form = Form(f)
        form.document_type_id = self.doc_type_with_validation
        form.save()
        self.assertEqual(f.annee_academique_id, self.annee)

    def test_reference_not_copied(self):
        """copy() does not copy reference field."""
        f = self._create_file(reference="REF-001")
        copied = f.copy()
        self.assertEqual(f.reference, "REF-001")
        self.assertFalse(copied.reference)
