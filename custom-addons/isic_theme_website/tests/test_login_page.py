"""Tests for isic_theme_website login page styling bridge."""

import odoo.tests


@odoo.tests.tagged("post_install", "-at_install")
class TestIsicLoginPage(odoo.tests.HttpCase):
    """Verify the ISIC-styled login page renders correctly."""

    def test_login_page_returns_200(self):
        """/web/login returns 200."""
        response = self.url_open("/web/login", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_login_page_contains_isic_branding(self):
        """/web/login contains ISIC branding text."""
        response = self.url_open("/web/login", timeout=30)
        self.assertIn(b"ISIC", response.content)

    def test_login_page_loads_css_assets(self):
        """/web/login loads frontend CSS assets."""
        response = self.url_open("/web/login", timeout=30)
        # The page should include a link to compiled frontend assets
        self.assertIn(b"assets", response.content)
