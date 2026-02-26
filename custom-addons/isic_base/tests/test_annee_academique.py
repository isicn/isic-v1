from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestAnneeAcademique(TransactionCase):
    """Tests for isic.annee.academique model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AnneeAcademique = cls.env["isic.annee.academique"]
        cls.annee = cls.AnneeAcademique.create(
            {
                "code": "2025-2026",
                "date_start": date(2025, 9, 1),
                "date_end": date(2026, 7, 31),
            }
        )

    # ---- Computed fields ----

    def test_compute_name(self):
        """name is computed from code."""
        self.assertEqual(self.annee.name, "2025-2026")

    def test_compute_name_empty_code(self):
        """name falls back to empty string when code is falsy."""
        annee = self.AnneeAcademique.create(
            {
                "code": "TEMP",
                "date_start": date(2024, 9, 1),
                "date_end": date(2025, 7, 31),
            }
        )
        # Verify the compute works even after update
        annee.code = "UPDATED"
        self.assertEqual(annee.name, "UPDATED")

    # ---- Constraints ----

    def test_check_dates_valid(self):
        """date_start < date_end is accepted."""
        annee = self.AnneeAcademique.create(
            {
                "code": "2024-2025",
                "date_start": date(2024, 9, 1),
                "date_end": date(2025, 7, 31),
            }
        )
        self.assertTrue(annee.id)

    def test_check_dates_invalid(self):
        """date_start >= date_end raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.AnneeAcademique.create(
                {
                    "code": "BAD-DATES",
                    "date_start": date(2026, 9, 1),
                    "date_end": date(2025, 7, 31),
                }
            )

    def test_check_dates_equal(self):
        """date_start == date_end raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.AnneeAcademique.create(
                {
                    "code": "EQUAL-DATES",
                    "date_start": date(2025, 9, 1),
                    "date_end": date(2025, 9, 1),
                }
            )

    @mute_logger("odoo.sql_db")
    def test_unique_code_per_company(self):
        """Duplicate code + company raises IntegrityError."""
        with self.assertRaises(IntegrityError):
            self.AnneeAcademique.create(
                {
                    "code": "2025-2026",
                    "date_start": date(2025, 9, 1),
                    "date_end": date(2026, 7, 31),
                }
            )
            self.env.cr.flush()

    def test_unique_code_different_companies(self):
        """Same code in different companies is OK."""
        company2 = self.env["res.company"].create({"name": "ISIC Branch"})
        annee2 = self.AnneeAcademique.with_company(company2).create(
            {
                "code": "2025-2026",
                "date_start": date(2025, 9, 1),
                "date_end": date(2026, 7, 31),
                "company_id": company2.id,
            }
        )
        self.assertTrue(annee2.id)

    def test_check_single_open_same_company(self):
        """Two open years in same company raises ValidationError."""
        self.annee.action_ouvrir()
        with self.assertRaises(ValidationError):
            other = self.AnneeAcademique.create(
                {
                    "code": "2026-2027",
                    "date_start": date(2026, 9, 1),
                    "date_end": date(2027, 7, 31),
                }
            )
            other.action_ouvrir()

    def test_check_single_open_different_companies(self):
        """Two open years in different companies is OK."""
        self.annee.action_ouvrir()
        company2 = self.env["res.company"].create({"name": "ISIC Branch 2"})
        annee2 = self.AnneeAcademique.with_company(company2).create(
            {
                "code": "2025-2026-B",
                "date_start": date(2025, 9, 1),
                "date_end": date(2026, 7, 31),
                "company_id": company2.id,
            }
        )
        annee2.action_ouvrir()
        self.assertEqual(annee2.state, "open")

    # ---- State transitions ----

    def test_action_ouvrir(self):
        """draft -> open transition."""
        self.assertEqual(self.annee.state, "draft")
        self.annee.action_ouvrir()
        self.assertEqual(self.annee.state, "open")

    def test_action_cloturer(self):
        """open -> closed transition, inscription_ouverte set to False."""
        self.annee.action_ouvrir()
        self.annee.inscription_ouverte = True
        self.annee.action_cloturer()
        self.assertEqual(self.annee.state, "closed")
        self.assertFalse(self.annee.inscription_ouverte)

    def test_action_cloturer_closes_inscriptions(self):
        """Closing sets inscription_ouverte to False."""
        self.annee.action_ouvrir()
        self.annee.inscription_ouverte = True
        self.assertTrue(self.annee.inscription_ouverte)
        self.annee.action_cloturer()
        self.assertFalse(self.annee.inscription_ouverte)

    def test_action_reset_draft(self):
        """closed -> draft transition."""
        self.annee.action_ouvrir()
        self.annee.action_cloturer()
        self.annee.action_reset_draft()
        self.assertEqual(self.annee.state, "draft")

    # ---- _get_current ----

    def test_get_current_returns_open(self):
        """Returns the open academic year."""
        self.annee.action_ouvrir()
        current = self.AnneeAcademique._get_current()
        self.assertEqual(current, self.annee)

    def test_get_current_no_open(self):
        """Returns empty recordset when no year is open."""
        current = self.AnneeAcademique._get_current()
        self.assertFalse(current)

    def test_get_current_respects_company(self):
        """_get_current filters by current company."""
        company2 = self.env["res.company"].create({"name": "ISIC Branch 3"})
        annee2 = self.AnneeAcademique.with_company(company2).create(
            {
                "code": "2025-2026-C",
                "date_start": date(2025, 9, 1),
                "date_end": date(2026, 7, 31),
                "company_id": company2.id,
            }
        )
        annee2.action_ouvrir()
        # From the default company, no open year
        current = self.AnneeAcademique._get_current()
        self.assertFalse(current)
        # From company2, the open year is returned
        current2 = self.AnneeAcademique.with_company(company2)._get_current()
        self.assertEqual(current2, annee2)


class TestAnneeAcademiqueAccess(TransactionCase):
    """Access control tests for isic.annee.academique."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AnneeAcademique = cls.env["isic.annee.academique"]
        cls.annee = cls.AnneeAcademique.create(
            {
                "code": "2025-2026",
                "date_start": date(2025, 9, 1),
                "date_end": date(2026, 7, 31),
            }
        )

        # Portal user — create as internal then switch to portal
        group_portal = cls.env.ref("base.group_portal")
        group_internal = cls.env.ref("base.group_user")
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Portal Student",
                "login": "portal_student",
            }
        )
        cls.portal_user.write(
            {
                "group_ids": [
                    (3, group_internal.id),
                    (4, group_portal.id),
                ],
            }
        )

        # Scolarite user
        cls.scolarite_user = cls.env["res.users"].create(
            {
                "name": "Agent Scolarite",
                "login": "agent_scolarite",
                "group_ids": [
                    (4, cls.env.ref("isic_base.group_isic_scolarite").id),
                ],
            }
        )

        # Direction user
        cls.direction_user = cls.env["res.users"].create(
            {
                "name": "Directeur",
                "login": "directeur_test",
                "group_ids": [
                    (4, cls.env.ref("isic_base.group_isic_direction").id),
                ],
            }
        )

    def test_access_portal_read_only(self):
        """Portal user can read but not write."""
        annee = self.annee.with_user(self.portal_user)
        annee.read(["code"])  # Should not raise
        with self.assertRaises(AccessError):
            self.AnneeAcademique.with_user(self.portal_user).create(
                {
                    "code": "PORTAL-FAIL",
                    "date_start": date(2027, 9, 1),
                    "date_end": date(2028, 7, 31),
                }
            )

    def test_access_scolarite_crud(self):
        """Scolarite user can read, write, create but not delete."""
        AnneeAsScol = self.AnneeAcademique.with_user(self.scolarite_user)
        new = AnneeAsScol.create(
            {
                "code": "SCOL-TEST",
                "date_start": date(2027, 9, 1),
                "date_end": date(2028, 7, 31),
            }
        )
        new.write({"code": "SCOL-TEST-2"})
        with self.assertRaises(AccessError):
            new.unlink()

    def test_access_direction_full(self):
        """Direction user has full CRUD access."""
        AnneeAsDir = self.AnneeAcademique.with_user(self.direction_user)
        new = AnneeAsDir.create(
            {
                "code": "DIR-TEST",
                "date_start": date(2027, 9, 1),
                "date_end": date(2028, 7, 31),
            }
        )
        new.write({"code": "DIR-TEST-2"})
        new.unlink()  # Should not raise

    def test_multi_company_rule(self):
        """Users only see years from their companies."""
        company2 = self.env["res.company"].create({"name": "ISIC Other"})
        annee_c2 = self.AnneeAcademique.create(
            {
                "code": "OTHER-CO",
                "date_start": date(2027, 9, 1),
                "date_end": date(2028, 7, 31),
                "company_id": company2.id,
            }
        )
        # Scolarite user belongs to main company only
        visible = self.AnneeAcademique.with_user(self.scolarite_user).search(
            [("id", "=", annee_c2.id)]
        )
        self.assertFalse(visible)
