from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    """Tests for res.users extensions in isic_base."""

    def test_create_auto_company_ids(self):
        """company_ids auto-set from company_id when not provided."""
        company = self.env.company
        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_auto_company",
                "company_id": company.id,
            }
        )
        self.assertIn(company, user.company_ids)

    def test_create_explicit_company_ids_not_overridden(self):
        """Explicit company_ids is preserved."""
        company1 = self.env.company
        company2 = self.env["res.company"].create({"name": "Company2"})
        user = self.env["res.users"].create(
            {
                "name": "Test User 2",
                "login": "test_explicit_companies",
                "company_id": company1.id,
                "company_ids": [(6, 0, [company1.id, company2.id])],
            }
        )
        self.assertEqual(len(user.company_ids), 2)
        self.assertIn(company2, user.company_ids)

    def test_create_without_uid_superuser_fix(self):
        """When env.uid is None, create uses SUPERUSER context (auth_ldap fix)."""
        Users = self.env["res.users"]
        # Simulate auth_ldap context where uid is None
        env_no_uid = Users.env(user=False)
        UsersNoUid = env_no_uid["res.users"]
        user = UsersNoUid.create(
            {
                "name": "LDAP User",
                "login": "ldap_test_user",
            }
        )
        self.assertTrue(user.id)

    def test_create_normal_uid_no_superuser(self):
        """Normal uid does not trigger SUPERUSER switch."""
        user = self.env["res.users"].create(
            {
                "name": "Normal User",
                "login": "normal_test_user",
            }
        )
        self.assertTrue(user.id)

    def test_matricule_field_exists(self):
        """matricule field is defined, indexed, copy=False."""
        field = self.env["res.users"]._fields.get("matricule")
        self.assertIsNotNone(field)
        self.assertTrue(field.index)
        self.assertFalse(field.copy)

    def test_matricule_not_copied(self):
        """copy() does not copy matricule."""
        user = self.env["res.users"].create(
            {
                "name": "User With Matricule",
                "login": "user_with_mat",
                "matricule": "MAT-001",
            }
        )
        copied = user.copy({"login": "user_with_mat_copy"})
        self.assertEqual(user.matricule, "MAT-001")
        self.assertFalse(copied.matricule)
