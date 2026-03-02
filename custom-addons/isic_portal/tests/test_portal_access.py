from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestPortalAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Demande = cls.env["isic.approbation.demande"]
        cls.Categorie = cls.env["isic.approbation.categorie"]

        # Portal user (student)
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Etudiant Test",
                "login": "etudiant_test_portal",
                "group_ids": [
                    (6, 0, [cls.env.ref("base.group_portal").id, cls.env.ref("isic_base.group_isic_etudiant").id]),
                ],
            }
        )

        # Second portal user
        cls.portal_user_2 = cls.env["res.users"].create(
            {
                "name": "Etudiant Test 2",
                "login": "etudiant_test_portal_2",
                "group_ids": [
                    (6, 0, [cls.env.ref("base.group_portal").id, cls.env.ref("isic_base.group_isic_etudiant").id]),
                ],
            }
        )

        # Category open to students
        cls.cat_att = cls.Categorie.create(
            {
                "name": "Attestation Test",
                "code": "ATT_TEST",
                "approbation_requise": False,
                "groupe_demandeur_ids": [(4, cls.env.ref("isic_base.group_isic_etudiant").id)],
            }
        )

        # Category NOT open to students
        cls.cat_restricted = cls.Categorie.create(
            {
                "name": "Restricted Test",
                "code": "RESTR_TEST",
                "approbation_requise": False,
                "groupe_demandeur_ids": [(4, cls.env.ref("base.group_user").id)],
            }
        )

        # Demande by portal user
        cls.demande_1 = cls.Demande.sudo().create(
            {
                "categorie_id": cls.cat_att.id,
                "demandeur_id": cls.portal_user.id,
                "motif": "Besoin attestation scolarite",
            }
        )

        # Demande by second portal user
        cls.demande_2 = cls.Demande.sudo().create(
            {
                "categorie_id": cls.cat_att.id,
                "demandeur_id": cls.portal_user_2.id,
                "motif": "Besoin attestation test",
            }
        )

    def test_portal_user_sees_own_demande(self):
        """Portal user can read their own demande."""
        demande = self.demande_1.with_user(self.portal_user)
        demande.read(["name", "motif", "state"])

    def test_portal_user_cannot_see_other_demande(self):
        """Portal user cannot read another user's demande."""
        demande = self.demande_2.with_user(self.portal_user)
        with self.assertRaises(AccessError):
            demande.read(["name", "motif", "state"])

    def test_portal_user_can_read_categories(self):
        """Portal user can read categories with matching groupe_demandeur_ids."""
        categories = self.Categorie.with_user(self.portal_user).search([("code", "=", "ATT_TEST")])
        self.assertEqual(len(categories), 1)

    def test_demande_has_access_url(self):
        """Demande with portal.mixin has correct access_url."""
        self.assertEqual(self.demande_1.access_url, f"/my/demandes/{self.demande_1.id}")

    def test_demande_has_access_token(self):
        """_portal_ensure_token() generates a token."""
        self.demande_1._portal_ensure_token()
        self.assertTrue(self.demande_1.access_token)
