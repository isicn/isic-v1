from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestApprobationDemande(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Demande = cls.env["isic.approbation.demande"]
        cls.Categorie = cls.env["isic.approbation.categorie"]
        cls.cat_conge = cls.Categorie.create(
            {
                "name": "Congé Test",
                "code": "TEST_CONGE",
                "approbation_requise": True,
            }
        )
        cls.cat_simple = cls.Categorie.create(
            {
                "name": "Simple Test",
                "code": "TEST_SIMPLE",
                "approbation_requise": False,
            }
        )

    def _create_demande(self, categorie=None, **kwargs):
        vals = {
            "categorie_id": (categorie or self.cat_conge).id,
            "motif": "Motif de test",
        }
        vals.update(kwargs)
        return self.Demande.create(vals)

    def test_create_default_values(self):
        """New request has default state=draft, name=/."""
        dem = self._create_demande()
        self.assertEqual(dem.state, "draft")
        self.assertEqual(dem.name, "/")
        self.assertEqual(dem.demandeur_id, self.env.user)

    def test_submit_generates_reference(self):
        """Submitting a request generates a sequence reference."""
        dem = self._create_demande()
        dem.action_submit()
        self.assertEqual(dem.state, "submitted")
        self.assertNotEqual(dem.name, "/")
        self.assertIn("TEST_CONGE", dem.name)

    def test_submit_only_from_draft(self):
        """Cannot submit a non-draft request."""
        dem = self._create_demande()
        dem.action_submit()
        with self.assertRaises(UserError):
            dem.action_submit()

    def test_cancel_from_draft(self):
        """Can cancel a draft request."""
        dem = self._create_demande()
        dem.action_cancel()
        self.assertEqual(dem.state, "cancelled")

    def test_cancel_from_submitted(self):
        """Can cancel a submitted request."""
        dem = self._create_demande()
        dem.action_submit()
        dem.action_cancel()
        self.assertEqual(dem.state, "cancelled")

    def test_cannot_cancel_approved(self):
        """Cannot cancel an approved request."""
        dem = self._create_demande()
        dem.write({"state": "approved", "name": "DEM/TEST/0001"})
        with self.assertRaises(UserError):
            dem.action_cancel()

    def test_reset_draft(self):
        """Reset to draft clears decision fields."""
        dem = self._create_demande()
        dem.write(
            {
                "state": "rejected",
                "name": "DEM/TEST/0002",
                "date_decision": "2026-01-01 00:00:00",
                "motif_refus": "Refusé",
            }
        )
        dem.action_reset_draft()
        self.assertEqual(dem.state, "draft")
        self.assertFalse(dem.date_decision)
        self.assertFalse(dem.motif_refus)

    def test_check_dates_valid(self):
        """Valid dates do not raise."""
        dem = self._create_demande(date_debut="2026-03-01", date_fin="2026-03-05")
        self.assertTrue(dem)

    def test_check_dates_invalid(self):
        """End date before start date raises UserError."""
        with self.assertRaises(UserError):
            self._create_demande(date_debut="2026-03-05", date_fin="2026-03-01")

    def test_submit_no_approbation(self):
        """Submit without approbation_requise does not call request_validation."""
        dem = self._create_demande(categorie=self.cat_simple)
        dem.action_submit()
        self.assertEqual(dem.state, "submitted")
        self.assertFalse(dem.review_ids)

    def test_action_approve(self):
        """action_approve sets state and date_decision."""
        dem = self._create_demande()
        dem.write({"state": "submitted", "name": "DEM/TEST/0003"})
        dem.action_approve()
        self.assertEqual(dem.state, "approved")
        self.assertTrue(dem.date_decision)

    def test_action_reject(self):
        """action_reject sets state, date_decision, and motif_refus."""
        dem = self._create_demande()
        dem.write({"state": "submitted", "name": "DEM/TEST/0004"})
        dem.action_reject(motif="Pas de budget")
        self.assertEqual(dem.state, "rejected")
        self.assertEqual(dem.motif_refus, "Pas de budget")
        self.assertTrue(dem.date_decision)
