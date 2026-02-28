from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase


class TestDashboardSection(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Section = cls.env["isic.dashboard.section"]
        cls.group_direction = cls.env.ref("isic_base.group_isic_direction")
        cls.group_scolarite = cls.env.ref("isic_base.group_isic_scolarite")

    def test_create_section(self):
        """A section can be created with minimal fields."""
        section = self.Section.create(
            {
                "name": "Test Section",
                "code": "test_create",
            }
        )
        self.assertTrue(section.active)
        self.assertEqual(section.icon, "fa-th-large")
        self.assertEqual(section.sequence, 10)

    def test_code_unique_constraint(self):
        """Two sections cannot share the same code."""
        self.Section.create({"name": "First", "code": "unique_test"})
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.Section.create({"name": "Second", "code": "unique_test"})

    def test_active_toggle(self):
        """Archiving a section hides it from default search."""
        section = self.Section.create({"name": "Toggle Test", "code": "toggle_test", "active": True})
        section.active = False
        # Default search excludes archived records
        found = self.Section.search([("code", "=", "toggle_test")])
        self.assertFalse(found)
        # Explicit search with active_test=False finds it
        found = self.Section.with_context(active_test=False).search([("code", "=", "toggle_test")])
        self.assertTrue(found)

    def test_group_ids_many2many(self):
        """group_ids correctly links to res.groups."""
        section = self.Section.create(
            {
                "name": "Restricted",
                "code": "restricted_test",
                "group_ids": [(4, self.group_direction.id), (4, self.group_scolarite.id)],
            }
        )
        self.assertEqual(len(section.group_ids), 2)
        self.assertIn(self.group_direction, section.group_ids)

    def test_default_sections_exist(self):
        """The 4 default sections are created by data XML."""
        for code in ("direction", "scolarite", "ged", "approbation"):
            section = self.Section.search([("code", "=", code)])
            self.assertTrue(section, f"Default section '{code}' not found")
