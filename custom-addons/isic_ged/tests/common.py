import base64
from datetime import date

from odoo.tests.common import TransactionCase


class IsicGedCase(TransactionCase):
    """Common setup for isic_ged tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Storage
        cls.storage = cls.env["dms.storage"].create(
            {"name": "Test GED Storage", "save_type": "database"}
        )
        # Access group with full perms for test user
        cls.access_group = cls.env["dms.access.group"].create(
            {
                "name": "Test Access",
                "perm_create": True,
                "perm_write": True,
                "perm_unlink": True,
            }
        )
        # Root directory
        cls.directory = cls.env["dms.directory"].create(
            {
                "name": "Test Root Dir",
                "is_root_directory": True,
                "storage_id": cls.storage.id,
                "group_ids": [(4, cls.access_group.id)],
            }
        )
        # Document types
        cls.doc_type_with_validation = cls.env["isic.document.type"].create(
            {
                "name": "PV Test",
                "code": "PV_TEST",
                "validation_required": True,
            }
        )
        cls.doc_type_without_validation = cls.env["isic.document.type"].create(
            {
                "name": "Divers Test",
                "code": "DIV_TEST",
                "validation_required": False,
            }
        )
        # Academic year
        cls.annee = cls.env["isic.annee.academique"].create(
            {
                "code": "2025-2026-GED",
                "date_start": date(2025, 9, 1),
                "date_end": date(2026, 7, 31),
                "state": "open",
            }
        )

    @classmethod
    def _create_file(cls, **kwargs):
        """Helper to create a dms.file with sensible defaults."""
        vals = {
            "name": "test_file.pdf",
            "directory_id": cls.directory.id,
            "content": base64.b64encode(b"test content"),
        }
        vals.update(kwargs)
        return cls.env["dms.file"].create(vals)
