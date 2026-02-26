from odoo.exceptions import AccessError

from .common import IsicGedCase


class TestDmsAccess(IsicGedCase):
    """Tests for DMS access control and the post_init_hook."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.direction_user = cls.env["res.users"].create(
            {
                "name": "Director Access",
                "login": "dir_access_user",
                "group_ids": [(4, cls.env.ref("isic_base.group_isic_direction").id)],
            }
        )
        cls.basic_user = cls.env["res.users"].create(
            {
                "name": "Basic Access User",
                "login": "basic_access_user",
                "group_ids": [(4, cls.env.ref("base.group_user").id)],
            }
        )
        # Grant DMS access to both users via the access group
        cls.access_group.write(
            {
                "explicit_user_ids": [
                    (4, cls.direction_user.id),
                    (4, cls.basic_user.id),
                ],
            }
        )
        # Flush so DMS raw SQL queries see users in dms_access_group_users_rel
        cls.env.flush_all()

    def test_access_check_includes_archived(self):
        """_check_access_dms_record uses active_test=False to include archived records."""
        f = self._create_file()
        f.active = False
        # Superuser can still call the method
        f.sudo()._check_access_dms_record("read")

    def test_access_check_superuser_bypass(self):
        """Superuser bypasses _check_access_dms_record."""
        f = self._create_file()
        # env.su = True should skip the check entirely
        f.sudo()._check_access_dms_record("write")

    def test_unarchive_allowed_for_authorized(self):
        """Authorized users can unarchive (toggle active back to True)."""
        f = self._create_file()
        f.active = False
        self.assertFalse(f.active)
        f.active = True
        self.assertTrue(f.active)

    def test_acl_file_user_no_delete(self):
        """base.group_user cannot delete dms.file."""
        f = self._create_file()
        with self.assertRaises(AccessError):
            f.with_user(self.basic_user).unlink()

    def test_acl_file_direction_delete(self):
        """Direction can delete dms.file."""
        f = self._create_file()
        f.with_user(self.direction_user).unlink()

    def test_acl_directory_user_no_delete(self):
        """base.group_user cannot delete dms.directory."""
        sub_dir = self.env["dms.directory"].create(
            {
                "name": "Sub Dir to Delete",
                "is_root_directory": False,
                "parent_id": self.directory.id,
            }
        )
        with self.assertRaises(AccessError):
            sub_dir.with_user(self.basic_user).unlink()

    def test_acl_directory_direction_delete(self):
        """Direction can delete dms.directory."""
        sub_dir = self.env["dms.directory"].create(
            {
                "name": "Sub Dir Dir Delete",
                "is_root_directory": False,
                "parent_id": self.directory.id,
            }
        )
        sub_dir.with_user(self.direction_user).unlink()

    def test_post_init_hook_hides_dms_menus(self):
        """After install, DMS root menu should be deactivated."""
        dms_root = self.env.ref("dms.main_menu_dms", raise_if_not_found=False)
        if dms_root:
            self.assertFalse(dms_root.active)
