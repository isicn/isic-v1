from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestPortalDemande(TransactionCase):
    """Test portal-specific demande behavior (model, mixin, access rules)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Demande = cls.env["isic.approbation.demande"]
        cls.Categorie = cls.env["isic.approbation.categorie"]

        # Portal user (student)
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Etudiant Demande Test",
                "login": "etudiant_demande_test",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_portal").id,
                            cls.env.ref("isic_base.group_isic_etudiant").id,
                        ],
                    )
                ],
            }
        )

        # Internal user
        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "Internal User Test",
                "login": "internal_demande_test",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )

        # Use existing ATT category or create one
        cls.cat_att = cls.Categorie.search([("code", "=", "ATT")], limit=1)
        if not cls.cat_att:
            cls.cat_att = cls.Categorie.create(
                {
                    "name": "Attestation Demande Test",
                    "code": "ATT",
                    "approbation_requise": False,
                    "groupe_demandeur_ids": [(4, cls.env.ref("isic_base.group_isic_etudiant").id)],
                }
            )
        # Ensure students can access this category
        etudiant_group = cls.env.ref("isic_base.group_isic_etudiant")
        if etudiant_group not in cls.cat_att.groupe_demandeur_ids:
            cls.cat_att.write({"groupe_demandeur_ids": [(4, etudiant_group.id)]})

        # Category NOT open to students (internal only) — unique code
        cls.cat_internal = cls.Categorie.search([("code", "=", "INTERN_TST")], limit=1)
        if not cls.cat_internal:
            cls.cat_internal = cls.Categorie.create(
                {
                    "name": "Internal Only Category",
                    "code": "INTERN_TST",
                    "approbation_requise": False,
                    "groupe_demandeur_ids": [(4, cls.env.ref("base.group_user").id)],
                }
            )

    # ------------------------------------------------------------------
    # Portal mixin
    # ------------------------------------------------------------------
    def test_access_url_format(self):
        """access_url follows /my/demandes/<id> format."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Test access_url",
            }
        )
        self.assertEqual(demande.access_url, f"/my/demandes/{demande.id}")

    def test_access_token_generated(self):
        """_portal_ensure_token generates a non-empty token."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Test token",
            }
        )
        demande._portal_ensure_token()
        self.assertTrue(demande.access_token)
        self.assertGreater(len(demande.access_token), 10)

    def test_mail_post_access_is_read(self):
        """Portal users can post messages with read access."""
        self.assertEqual(self.Demande._mail_post_access, "read")

    # ------------------------------------------------------------------
    # Portal create via sudo (mimics controller flow)
    # ------------------------------------------------------------------
    def test_sudo_create_sets_demandeur(self):
        """Creating via sudo with explicit demandeur_id works."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Via portal form",
            }
        )
        self.assertEqual(demande.demandeur_id, self.portal_user)
        self.assertEqual(demande.state, "draft")

    def test_sudo_create_and_submit(self):
        """Create + action_submit auto-submits the demande (portal flow)."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Auto-submit test",
            }
        )
        demande.action_submit()
        self.assertEqual(demande.state, "submitted")
        self.assertNotEqual(demande.name, "/", "Reference should be generated on submit")

    def test_sudo_create_with_dates(self):
        """Dates are properly stored."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Date test",
                "date_debut": "2026-04-01",
                "date_fin": "2026-04-15",
            }
        )
        self.assertEqual(str(demande.date_debut), "2026-04-01")
        self.assertEqual(str(demande.date_fin), "2026-04-15")

    def test_sudo_create_with_priority(self):
        """Priority field accepts valid values."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Urgent request",
                "priorite": "1",
            }
        )
        self.assertEqual(demande.priorite, "1")

    def test_sudo_create_with_observations(self):
        """Observations field stored correctly."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Obs test",
                "observations": "Some details here",
            }
        )
        self.assertEqual(demande.observations, "Some details here")

    # ------------------------------------------------------------------
    # Access rules for portal
    # ------------------------------------------------------------------
    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_portal_user_sees_own_demandes(self):
        """Portal user can search their own demandes."""
        self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "My demande",
            }
        )
        demandes = self.Demande.with_user(self.portal_user).search([])
        self.assertTrue(all(d.demandeur_id == self.portal_user for d in demandes))

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_portal_user_cannot_see_others(self):
        """Portal user cannot see demandes of other users."""
        other_demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.internal_user.id,
                "motif": "Not for portal",
            }
        )
        with self.assertRaises(AccessError):
            other_demande.with_user(self.portal_user).read(["motif"])

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_portal_user_cannot_create(self):
        """Portal user cannot create demandes directly (only via sudo)."""
        with self.assertRaises(AccessError):
            self.Demande.with_user(self.portal_user).create(
                {
                    "categorie_id": self.cat_att.id,
                    "motif": "Should fail",
                }
            )

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_portal_user_cannot_write(self):
        """Portal user cannot write demandes directly."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Read only",
            }
        )
        with self.assertRaises(AccessError):
            demande.with_user(self.portal_user).write({"motif": "Modified"})

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_portal_user_cannot_unlink(self):
        """Portal user cannot delete demandes."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Cannot delete",
            }
        )
        with self.assertRaises(AccessError):
            demande.with_user(self.portal_user).unlink()

    # ------------------------------------------------------------------
    # Category access rules
    # ------------------------------------------------------------------
    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_portal_sees_matching_categories(self):
        """Portal user sees categories matching their group."""
        cats = self.Categorie.with_user(self.portal_user).search([("code", "=", "ATT")])
        self.assertEqual(len(cats), 1)

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_portal_cannot_see_internal_categories(self):
        """Portal user cannot see categories restricted to internal group."""
        cats = self.Categorie.with_user(self.portal_user).search([("code", "=", "INTERN_TST")])
        self.assertFalse(cats, "Portal user should not see internal-only categories")

    # ------------------------------------------------------------------
    # Submit validation (unauthorized category)
    # ------------------------------------------------------------------
    def test_submit_unauthorized_category_raises(self):
        """Submitting a demande with unauthorized category raises."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_internal.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Should fail on submit",
            }
        )
        with self.assertRaises(UserError):
            demande.action_submit()

    # ------------------------------------------------------------------
    # Date validation
    # ------------------------------------------------------------------
    def test_date_fin_before_debut_raises(self):
        """Date fin before date debut raises ValidationError."""
        from odoo.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            self.Demande.sudo().create(
                {
                    "categorie_id": self.cat_att.id,
                    "demandeur_id": self.portal_user.id,
                    "motif": "Bad dates",
                    "date_debut": "2026-04-15",
                    "date_fin": "2026-04-01",
                }
            )

    # ------------------------------------------------------------------
    # Workflow transitions visible from portal
    # ------------------------------------------------------------------
    def test_cancel_submitted_demande(self):
        """Cancelling a submitted demande works."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Will cancel",
            }
        )
        demande.action_submit()
        demande.action_cancel()
        self.assertEqual(demande.state, "cancelled")

    def test_cancel_approved_raises(self):
        """Cannot cancel an approved demande."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Will approve then try cancel",
            }
        )
        demande.action_submit()
        demande.action_approve()
        with self.assertRaises(UserError):
            demande.action_cancel()


class TestPortalDocuments(TransactionCase):
    """Test portal document access (DMS files filtered by partner_id)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.DmsFile = cls.env["dms.file"]
        cls.DocType = cls.env["isic.document.type"]

        # Portal user
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Etudiant Doc Test",
                "login": "etudiant_doc_test",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_portal").id,
                            cls.env.ref("isic_base.group_isic_etudiant").id,
                        ],
                    )
                ],
            }
        )

        # Second portal user
        cls.portal_user_2 = cls.env["res.users"].create(
            {
                "name": "Etudiant Doc Test 2",
                "login": "etudiant_doc_test_2",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_portal").id,
                            cls.env.ref("isic_base.group_isic_etudiant").id,
                        ],
                    )
                ],
            }
        )

        # Create storage + directory
        cls.storage = cls.env["dms.storage"].create(
            {
                "name": "Portal Test Storage",
                "save_type": "database",
            }
        )
        cls.directory = cls.env["dms.directory"].create(
            {
                "name": "Portal Test Dir",
                "storage_id": cls.storage.id,
                "is_root_directory": True,
            }
        )

        # Create document type (unique code to avoid collisions)
        cls.doc_type = cls.DocType.search([("code", "=", "PTST_DOC")], limit=1)
        if not cls.doc_type:
            cls.doc_type = cls.DocType.create(
                {
                    "name": "Portal Test Doc Type",
                    "code": "PTST_DOC",
                    "retention_days": 1825,
                }
            )

        # File for portal_user (validated)
        cls.file_user_1 = cls.DmsFile.sudo().create(
            {
                "name": "attestation_user1.pdf",
                "directory_id": cls.directory.id,
                "content": "dGVzdA==",  # base64 "test"
                "partner_id": cls.portal_user.partner_id.id,
                "document_type_id": cls.doc_type.id,
                "ged_state": "validated",
            }
        )

        # File for portal_user (draft — should be hidden)
        cls.file_user_1_draft = cls.DmsFile.sudo().create(
            {
                "name": "draft_user1.pdf",
                "directory_id": cls.directory.id,
                "content": "dGVzdA==",
                "partner_id": cls.portal_user.partner_id.id,
                "document_type_id": cls.doc_type.id,
                "ged_state": "draft",
            }
        )

        # File for portal_user_2 (validated — should NOT be visible to user 1)
        cls.file_user_2 = cls.DmsFile.sudo().create(
            {
                "name": "attestation_user2.pdf",
                "directory_id": cls.directory.id,
                "content": "dGVzdA==",
                "partner_id": cls.portal_user_2.partner_id.id,
                "document_type_id": cls.doc_type.id,
                "ged_state": "validated",
            }
        )

    # ------------------------------------------------------------------
    # Document count by partner_id
    # ------------------------------------------------------------------
    def test_document_count_own_non_draft(self):
        """Document count returns only own non-draft files."""
        partner_id = self.portal_user.partner_id.id
        domain = [("partner_id", "=", partner_id), ("ged_state", "!=", "draft")]
        count = self.DmsFile.sudo().search_count(domain)
        self.assertEqual(count, 1, "Should only count 1 validated file for user 1")

    def test_document_count_excludes_other_user(self):
        """Document count does not include other user's files."""
        partner_id = self.portal_user.partner_id.id
        domain = [("partner_id", "=", partner_id)]
        files = self.DmsFile.sudo().search(domain)
        self.assertTrue(all(f.partner_id.id == partner_id for f in files))

    def test_document_count_excludes_drafts(self):
        """Draft documents are excluded from portal count."""
        partner_id = self.portal_user.partner_id.id
        domain = [("partner_id", "=", partner_id), ("ged_state", "!=", "draft")]
        files = self.DmsFile.sudo().search(domain)
        self.assertTrue(all(f.ged_state != "draft" for f in files))

    # ------------------------------------------------------------------
    # Document filtering
    # ------------------------------------------------------------------
    def test_filter_by_type(self):
        """Filtering by document type narrows results."""
        partner_id = self.portal_user.partner_id.id
        domain = [
            ("partner_id", "=", partner_id),
            ("ged_state", "!=", "draft"),
            ("document_type_id", "=", self.doc_type.id),
        ]
        files = self.DmsFile.sudo().search(domain)
        self.assertEqual(len(files), 1)

    def test_filter_by_state_validated(self):
        """Filtering by validated state returns correct files."""
        partner_id = self.portal_user.partner_id.id
        domain = [
            ("partner_id", "=", partner_id),
            ("ged_state", "=", "validated"),
        ]
        files = self.DmsFile.sudo().search(domain)
        self.assertEqual(len(files), 1)
        self.assertEqual(files.name, "attestation_user1.pdf")

    def test_search_by_name(self):
        """Search by name filters correctly."""
        partner_id = self.portal_user.partner_id.id
        domain = [
            ("partner_id", "=", partner_id),
            ("ged_state", "!=", "draft"),
            ("name", "ilike", "attestation"),
        ]
        files = self.DmsFile.sudo().search(domain)
        self.assertEqual(len(files), 1)

    def test_search_no_match(self):
        """Search with non-matching term returns empty."""
        partner_id = self.portal_user.partner_id.id
        domain = [
            ("partner_id", "=", partner_id),
            ("ged_state", "!=", "draft"),
            ("name", "ilike", "nonexistent"),
        ]
        files = self.DmsFile.sudo().search(domain)
        self.assertFalse(files)

    # ------------------------------------------------------------------
    # DMS portal filter (draft hiding)
    # ------------------------------------------------------------------
    def test_dms_portal_hides_drafts(self):
        """Portal user's file list excludes draft documents."""
        partner_id = self.portal_user.partner_id.id
        # Simulate the controller domain
        domain = [("partner_id", "=", partner_id), ("ged_state", "!=", "draft")]
        files = self.DmsFile.sudo().search(domain)
        for f in files:
            self.assertNotEqual(f.ged_state, "draft", f"Draft file {f.name} should be hidden")

    # ------------------------------------------------------------------
    # Document type access for portal
    # ------------------------------------------------------------------
    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_portal_can_read_document_types(self):
        """Portal user can read document types (for filter dropdown)."""
        doc_types = self.DocType.with_user(self.portal_user).search([("active", "=", True)])
        self.assertTrue(doc_types, "Portal user should be able to read document types")
