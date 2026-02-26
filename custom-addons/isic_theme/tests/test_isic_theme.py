from odoo.tests.common import TransactionCase


class TestIsicThemeHook(TransactionCase):
    """Tests for isic_theme post_init_hook effects."""

    def test_post_init_hook_sets_company_name(self):
        """Main company name is set to 'ISIC' by post_init_hook."""
        main_company = self.env.ref("base.main_company")
        self.assertEqual(main_company.name, "ISIC")

    def test_post_init_hook_sets_company_logo(self):
        """Main company logo is set by post_init_hook."""
        main_company = self.env.ref("base.main_company")
        self.assertTrue(main_company.logo)

    def test_post_init_hook_hides_sidebar(self):
        """sidebar_type is set to 'invisible' for all users."""
        users_with_sidebar = self.env["res.users"].search(
            [("sidebar_type", "!=", "invisible")]
        )
        self.assertFalse(users_with_sidebar)


class TestIsicThemeColorScheme(TransactionCase):
    """Tests for color_scheme field on res.users."""

    def test_color_scheme_default(self):
        """Default color_scheme is 'light'."""
        user = self.env["res.users"].create(
            {
                "name": "Theme User",
                "login": "theme_user",
            }
        )
        self.assertEqual(user.color_scheme, "light")

    def test_color_scheme_dark(self):
        """color_scheme can be set to 'dark'."""
        user = self.env["res.users"].create(
            {
                "name": "Dark User",
                "login": "dark_user",
            }
        )
        user.color_scheme = "dark"
        self.assertEqual(user.color_scheme, "dark")

    def test_color_scheme_self_readable(self):
        """color_scheme is in SELF_READABLE_FIELDS."""
        user = self.env["res.users"].create(
            {
                "name": "Readable User",
                "login": "readable_user",
            }
        )
        self.assertIn("color_scheme", user.SELF_READABLE_FIELDS)

    def test_color_scheme_self_writable(self):
        """color_scheme is in SELF_WRITEABLE_FIELDS."""
        user = self.env["res.users"].create(
            {
                "name": "Writable User",
                "login": "writable_user",
            }
        )
        self.assertIn("color_scheme", user.SELF_WRITEABLE_FIELDS)

    def test_ir_http_color_scheme(self):
        """IrHttp.color_scheme() returns user's scheme (tested without HTTP request)."""
        # Without request context, the method returns "light" (fallback)
        ir_http = self.env["ir.http"]
        result = ir_http.color_scheme()
        self.assertEqual(result, "light")
