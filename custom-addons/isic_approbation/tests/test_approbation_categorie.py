from psycopg2 import IntegrityError

from odoo.addons.isic_approbation import _extract_categorie_id, _post_init_hook
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestApprobationCategorie(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Categorie = cls.env["isic.approbation.categorie"]

    def test_create_categorie_with_sequence(self):
        """Creating a category auto-creates an ir.sequence."""
        cat = self.Categorie.create(
            {
                "name": "Test Catégorie",
                "code": "TEST_SEQ",
            }
        )
        self.assertTrue(cat.sequence_id)
        self.assertIn("TEST_SEQ", cat.sequence_id.prefix)

    @mute_logger("odoo.sql_db")
    def test_unique_code_constraint(self):
        """Duplicate code raises IntegrityError."""
        self.Categorie.create({"name": "Cat A", "code": "UNIQUE_A"})
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.Categorie.create({"name": "Cat B", "code": "UNIQUE_A"})

    def test_default_values(self):
        """Check default field values."""
        cat = self.Categorie.create({"name": "Défauts", "code": "DEFAULTS"})
        self.assertTrue(cat.active)
        self.assertTrue(cat.approbation_requise)
        self.assertEqual(cat.nombre_niveaux, 1)
        self.assertEqual(cat.delai_traitement, 5)
        self.assertEqual(cat.sequence, 10)

    def test_demande_count(self):
        """demande_count is computed from related requests."""
        cat = self.Categorie.create({"name": "Count", "code": "COUNT"})
        self.assertEqual(cat.demande_count, 0)
        self.env["isic.approbation.demande"].create(
            {
                "categorie_id": cat.id,
                "motif": "Test compteur",
            }
        )
        cat.invalidate_recordset(["demande_count"])
        self.assertEqual(cat.demande_count, 1)


class TestApprobateurSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Categorie = cls.env["isic.approbation.categorie"]
        cls.TierDef = cls.env["tier.definition"]
        cls.Demande = cls.env["isic.approbation.demande"]
        cls.group_dept = cls.env.ref("isic_base.group_isic_departement")
        cls.group_sg = cls.env.ref("isic_base.group_isic_secretariat")

    def test_create_categorie_with_approbateurs(self):
        """Creating a category with inline approbateurs creates tier.definition records."""
        cat = self.Categorie.create(
            {
                "name": "Sync Test",
                "code": "SYNC_CREATE",
                "approbateur_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "review_type": "group",
                            "reviewer_group_id": self.group_dept.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 20,
                            "review_type": "group",
                            "reviewer_group_id": self.group_sg.id,
                        },
                    ),
                ],
            }
        )
        self.assertEqual(len(cat.approbateur_ids), 2)
        # Both should have tier_definition_id set
        for appro in cat.approbateur_ids:
            self.assertTrue(appro.tier_definition_id, f"Missing tier for {appro.name}")
        # First approbateur (seq 10) should get higher tier sequence (approves first)
        appro1 = cat.approbateur_ids.sorted("sequence")[0]
        appro2 = cat.approbateur_ids.sorted("sequence")[1]
        self.assertGreater(appro1.tier_definition_id.sequence, appro2.tier_definition_id.sequence)
        # approve_sequence should be True (multiple approvers)
        self.assertTrue(appro1.tier_definition_id.approve_sequence)

    def test_update_approbateur(self):
        """Modifying an approbateur updates its tier.definition."""
        cat = self.Categorie.create(
            {
                "name": "Sync Update",
                "code": "SYNC_UPDATE",
                "approbateur_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "review_type": "group",
                            "reviewer_group_id": self.group_dept.id,
                            "has_comment": True,
                        },
                    ),
                ],
            }
        )
        appro = cat.approbateur_ids
        tier = appro.tier_definition_id
        self.assertTrue(tier.has_comment)

        # Update the approbateur's group
        cat.write(
            {
                "approbateur_ids": [
                    (1, appro.id, {"reviewer_group_id": self.group_sg.id, "has_comment": False}),
                ],
            }
        )
        tier = appro.tier_definition_id
        self.assertEqual(tier.reviewer_group_id, self.group_sg)
        self.assertFalse(tier.has_comment)

    def test_delete_approbateur(self):
        """Deleting an approbateur removes its tier.definition."""
        cat = self.Categorie.create(
            {
                "name": "Sync Delete",
                "code": "SYNC_DEL",
                "approbateur_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "review_type": "group",
                            "reviewer_group_id": self.group_dept.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 20,
                            "review_type": "group",
                            "reviewer_group_id": self.group_sg.id,
                        },
                    ),
                ],
            }
        )
        self.assertEqual(len(cat.approbateur_ids), 2)
        tier_to_delete = cat.approbateur_ids.sorted("sequence")[1].tier_definition_id
        tier_id = tier_to_delete.id

        # Remove second approbateur via unlink
        cat.approbateur_ids.sorted("sequence")[1].unlink()
        self.assertEqual(len(cat.approbateur_ids), 1)
        # The tier.definition should be deleted
        self.assertFalse(self.TierDef.browse(tier_id).exists())

    def test_submit_uses_inline_tiers(self):
        """Submitting a demande uses tier.definitions created from approbateurs."""
        cat = self.Categorie.create(
            {
                "name": "Sync Submit",
                "code": "SYNC_SUBMIT",
                "approbation_requise": True,
                "approbateur_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "review_type": "group",
                            "reviewer_group_id": self.group_dept.id,
                        },
                    ),
                ],
            }
        )
        dem = self.Demande.create(
            {
                "categorie_id": cat.id,
                "motif": "Test inline tiers",
            }
        )
        dem.action_submit()
        self.assertEqual(dem.state, "submitted")
        # Should have review_ids from our inline tier
        self.assertTrue(dem.review_ids)
        self.assertEqual(len(dem.review_ids), 1)

    def test_single_approbateur_no_approve_sequence(self):
        """A single approbateur should not set approve_sequence."""
        cat = self.Categorie.create(
            {
                "name": "Single",
                "code": "SYNC_SINGLE",
                "approbateur_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "review_type": "group",
                            "reviewer_group_id": self.group_dept.id,
                        },
                    ),
                ],
            }
        )
        tier = cat.approbateur_ids[0].tier_definition_id
        self.assertFalse(tier.approve_sequence)


class TestPostInitMigration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Categorie = cls.env["isic.approbation.categorie"]
        cls.TierDef = cls.env["tier.definition"]
        cls.Approbateur = cls.env["isic.approbation.approbateur"]
        cls.group_dept = cls.env.ref("isic_base.group_isic_departement")
        cls.group_sg = cls.env.ref("isic_base.group_isic_secretariat")

    def test_extract_categorie_id_by_code(self):
        """_extract_categorie_id parses categorie_id.code domain."""
        cat = self.Categorie.create({"name": "Extract Code", "code": "EX_CODE"})
        domain_str = "[('categorie_id.code', '=', 'EX_CODE')]"
        result = _extract_categorie_id(domain_str, self.Categorie)
        self.assertEqual(result, cat.id)

    def test_extract_categorie_id_by_id(self):
        """_extract_categorie_id parses categorie_id direct domain."""
        domain_str = "[('categorie_id', '=', 42)]"
        result = _extract_categorie_id(domain_str, self.Categorie)
        self.assertEqual(result, 42)

    def test_extract_categorie_id_invalid(self):
        """_extract_categorie_id returns False for invalid domains."""
        self.assertFalse(_extract_categorie_id("", self.Categorie))
        self.assertFalse(_extract_categorie_id("not a domain", self.Categorie))
        self.assertFalse(_extract_categorie_id("[('other_field', '=', 1)]", self.Categorie))

    def test_post_init_hook_migrates_tiers(self):
        """_post_init_hook creates approbateur records from existing tier.definition."""
        cat = self.Categorie.create({"name": "Migration", "code": "MIGRATE"})
        model_id = self.env["ir.model"]._get_id("isic.approbation.demande")

        # Create tier.definition records manually (simulating pre-migration state)
        tier1 = self.TierDef.create(
            {
                "name": "Migrate L1",
                "model_id": model_id,
                "review_type": "group",
                "reviewer_group_id": self.group_dept.id,
                "definition_domain": f"[('categorie_id', '=', {cat.id})]",
                "sequence": 20,
                "has_comment": True,
            }
        )
        tier2 = self.TierDef.create(
            {
                "name": "Migrate L2",
                "model_id": model_id,
                "review_type": "group",
                "reviewer_group_id": self.group_sg.id,
                "definition_domain": f"[('categorie_id', '=', {cat.id})]",
                "sequence": 10,
                "has_comment": False,
            }
        )

        # Run hook
        _post_init_hook(self.env)

        # Check approbateurs were created
        appros = self.Approbateur.search([("categorie_id", "=", cat.id)], order="sequence")
        self.assertEqual(len(appros), 2)
        # First appro (from tier with highest seq=20, processed first) should link to tier1
        self.assertEqual(appros[0].tier_definition_id, tier1)
        self.assertEqual(appros[0].reviewer_group_id, self.group_dept)
        self.assertTrue(appros[0].has_comment)
        # Second appro should link to tier2
        self.assertEqual(appros[1].tier_definition_id, tier2)
        self.assertEqual(appros[1].reviewer_group_id, self.group_sg)
        self.assertFalse(appros[1].has_comment)

    def test_post_init_hook_idempotent(self):
        """Running _post_init_hook twice does not duplicate approbateurs."""
        cat = self.Categorie.create({"name": "Idempotent", "code": "IDEMP"})
        model_id = self.env["ir.model"]._get_id("isic.approbation.demande")
        self.TierDef.create(
            {
                "name": "Idemp L1",
                "model_id": model_id,
                "review_type": "group",
                "reviewer_group_id": self.group_dept.id,
                "definition_domain": f"[('categorie_id', '=', {cat.id})]",
                "sequence": 10,
            }
        )

        _post_init_hook(self.env)
        count1 = self.Approbateur.search_count([("categorie_id", "=", cat.id)])

        _post_init_hook(self.env)
        count2 = self.Approbateur.search_count([("categorie_id", "=", cat.id)])

        self.assertEqual(count1, count2)
