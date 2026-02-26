from psycopg2 import IntegrityError

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
