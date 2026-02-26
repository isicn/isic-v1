from odoo.exceptions import AccessDenied

from .common import CASTestCase


class TestCASSigninCreate(CASTestCase):
    """Tests for CAS user creation via _cas_signin."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Mapping: faculty -> enseignant (internal)
        cls._create_mapping(
            cas_attribute="employeeType",
            cas_value="faculty",
            odoo_group_id=cls.group_enseignant.id,
            is_internal_user=True,
            sequence=10,
        )
        # Mapping: student -> etudiant (portal)
        cls._create_mapping(
            cas_attribute="employeeType",
            cas_value="student",
            odoo_group_id=cls.group_etudiant.id,
            is_internal_user=False,
            sequence=20,
        )

    def test_cas_create_user_internal(self):
        """New internal user is created from CAS attributes."""
        validation = {
            "user": "prof.test",
            "uid": "prof.test",
            "mail": "prof.test@isic.ac.ma",
            "cn": "Prof Test",
            "employeeType": "faculty",
        }
        login = self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        self.assertEqual(login, "prof.test")
        user = self.env["res.users"].sudo().search([("login", "=", "prof.test")])
        self.assertTrue(user)
        self.assertIn(self.group_enseignant, user.group_ids)

    def test_cas_create_user_portal(self):
        """New portal user is created for student."""
        validation = {
            "user": "etudiant.test",
            "uid": "etudiant.test",
            "mail": "etudiant.test@isic.ac.ma",
            "cn": "Etudiant Test",
            "employeeType": "student",
        }
        login = self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        self.assertEqual(login, "etudiant.test")
        user = self.env["res.users"].sudo().search([("login", "=", "etudiant.test")])
        portal_group = self.env.ref("base.group_portal")
        self.assertIn(portal_group, user.group_ids)

    def test_cas_create_user_fields(self):
        """All CAS fields are populated on the new user."""
        validation = {
            "user": "agent.fields",
            "uid": "agent.fields",
            "mail": "agent.fields@isic.ac.ma",
            "cn": "Agent Fields",
            "employeeType": "faculty",
        }
        self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        user = self.env["res.users"].sudo().search([("login", "=", "agent.fields")])
        self.assertEqual(user.cas_uid, "agent.fields")
        self.assertEqual(user.oauth_uid, "agent.fields")
        self.assertEqual(user.oauth_provider_id, self.cas_provider)
        self.assertTrue(user.cas_attributes)
        self.assertTrue(user.cas_last_sync)

    def test_cas_create_user_email_as_list(self):
        """Email returned as list is normalized to string."""
        validation = {
            "user": "list.email",
            "uid": "list.email",
            "mail": ["list.email@isic.ac.ma"],
            "cn": "List Email",
            "employeeType": "faculty",
        }
        login = self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        user = self.env["res.users"].sudo().search([("login", "=", login)])
        self.assertEqual(user.email, "list.email@isic.ac.ma")

    def test_cas_create_user_groups_assigned(self):
        """ISIC groups from mapping are assigned to new user."""
        validation = {
            "user": "prof.groups",
            "uid": "prof.groups",
            "mail": "prof.groups@isic.ac.ma",
            "cn": "Prof Groups",
            "employeeType": "faculty",
        }
        self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        user = self.env["res.users"].sudo().search([("login", "=", "prof.groups")])
        self.assertIn(self.group_enseignant, user.group_ids)


class TestCASSigninUpdate(CASTestCase):
    """Tests for CAS user update on subsequent logins."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_mapping(
            cas_attribute="employeeType",
            cas_value="faculty",
            odoo_group_id=cls.group_enseignant.id,
            is_internal_user=True,
            sequence=10,
        )

    def test_cas_update_existing_by_oauth_uid(self):
        """Finds existing user by oauth_uid."""
        user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": "Existing OAuth",
                    "login": "existing.oauth",
                    "oauth_provider_id": self.cas_provider.id,
                    "oauth_uid": "existing.oauth",
                    "cas_uid": "existing.oauth",
                }
            )
        )
        validation = {
            "user": "existing.oauth",
            "uid": "existing.oauth",
            "mail": "existing@isic.ac.ma",
            "cn": "Existing OAuth",
            "employeeType": "faculty",
        }
        login = self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        self.assertEqual(login, user.login)

    def test_cas_update_existing_by_login(self):
        """Finds existing user by login matching cas_uid."""
        user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": "Login Match",
                    "login": "login.match",
                }
            )
        )
        validation = {
            "user": "login.match",
            "uid": "login.match",
            "mail": "login.match@isic.ac.ma",
            "cn": "Login Match",
            "employeeType": "faculty",
        }
        login = self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        self.assertEqual(login, user.login)

    def test_cas_update_existing_by_email(self):
        """Finds existing user by email when login doesn't match."""
        user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": "Email Match",
                    "login": "email.match",
                    "email": "email.match@isic.ac.ma",
                }
            )
        )
        validation = {
            "user": "different_uid",
            "uid": "different_uid",
            "mail": "email.match@isic.ac.ma",
            "cn": "Email Match",
            "employeeType": "faculty",
        }
        login = self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        self.assertEqual(login, user.login)

    def test_cas_update_syncs_groups(self):
        """Groups are synced on update."""
        user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": "Sync Groups",
                    "login": "sync.groups",
                    "oauth_provider_id": self.cas_provider.id,
                    "oauth_uid": "sync.groups",
                    "cas_uid": "sync.groups",
                }
            )
        )
        validation = {
            "user": "sync.groups",
            "uid": "sync.groups",
            "mail": "sync@isic.ac.ma",
            "cn": "Sync Groups",
            "employeeType": "faculty",
        }
        self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        user.invalidate_recordset()
        self.assertIn(self.group_enseignant, user.group_ids)

    def test_cas_signin_missing_uid_raises(self):
        """Missing UID in validation raises AccessDenied."""
        validation = {"mail": "nouid@isic.ac.ma", "cn": "No UID"}
        with self.assertRaises(AccessDenied):
            self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
