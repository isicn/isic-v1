from psycopg2 import IntegrityError

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestDocumentType(TransactionCase):
    """Tests for isic.document.type model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.DocType = cls.env["isic.document.type"]

    def test_create_document_type(self):
        """Basic CRUD works."""
        dt = self.DocType.create({"name": "Test Type", "code": "TST"})
        self.assertTrue(dt.id)
        self.assertEqual(dt.name, "Test Type")
        self.assertEqual(dt.code, "TST")

    @mute_logger("odoo.sql_db")
    def test_code_unique_constraint(self):
        """Duplicate code raises IntegrityError."""
        self.DocType.create({"name": "Type A", "code": "UNIQ"})
        with self.assertRaises(IntegrityError):
            self.DocType.create({"name": "Type B", "code": "UNIQ"})
            self.env.cr.flush()

    @mute_logger("odoo.sql_db")
    def test_required_code(self):
        """code is required — raises IntegrityError at DB level."""
        with self.assertRaises(IntegrityError):
            self.DocType.create({"name": "No Code"})

    @mute_logger("odoo.sql_db")
    def test_required_name(self):
        """name is required — raises IntegrityError at DB level."""
        with self.assertRaises(IntegrityError):
            self.DocType.create({"code": "NO_NAME"})

    def test_defaults(self):
        """Default values: active=True, validation_required=False, sequence=10."""
        dt = self.DocType.create({"name": "Defaults", "code": "DEF"})
        self.assertTrue(dt.active)
        self.assertFalse(dt.validation_required)
        self.assertEqual(dt.sequence, 10)

    def test_ordering_by_sequence(self):
        """Records are ordered by sequence, then name."""
        dt1 = self.DocType.create({"name": "Zebra", "code": "Z1", "sequence": 1})
        self.DocType.create({"name": "Alpha", "code": "A1", "sequence": 2})
        results = self.DocType.search([("code", "in", ["Z1", "A1"])])
        self.assertEqual(results[0], dt1)  # seq 1 before seq 2

    def test_acl_user_read_only(self):
        """base.group_user can read but not create."""
        user = self.env["res.users"].create(
            {
                "name": "Basic User",
                "login": "basic_dt_user",
                "group_ids": [(4, self.env.ref("base.group_user").id)],
            }
        )
        # Read OK
        self.DocType.with_user(user).search([])
        # Create denied
        with self.assertRaises(AccessError):
            self.DocType.with_user(user).create({"name": "Fail", "code": "FAIL"})

    def test_acl_direction_full_crud(self):
        """Direction can create, read, write, delete."""
        user = self.env["res.users"].create(
            {
                "name": "Director DT",
                "login": "dir_dt_user",
                "group_ids": [(4, self.env.ref("isic_base.group_isic_direction").id)],
            }
        )
        dt = self.DocType.with_user(user).create({"name": "Dir Type", "code": "DDIR"})
        dt.write({"name": "Dir Type Updated"})
        dt.unlink()
