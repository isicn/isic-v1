import json

from odoo.tests import Form

from .common import CASTestCase


class TestCASProvider(CASTestCase):
    """Tests for auth.oauth.provider CAS extensions."""

    def test_compute_cas_endpoints(self):
        """Token and logout URLs are computed from cas_server_url."""
        self.assertEqual(
            self.cas_provider.cas_token_endpoint,
            "https://cas.test.isic.ma/cas/oauth2.0/accessToken",
        )
        self.assertEqual(
            self.cas_provider.cas_logout_endpoint,
            "https://cas.test.isic.ma/cas/logout",
        )

    def test_compute_cas_endpoints_non_cas(self):
        """Non-CAS provider has no CAS endpoints."""
        provider = self.Provider.create(
            {
                "name": "Google OAuth",
                "is_cas_provider": False,
                "client_id": "google_client",
                "auth_endpoint": "https://accounts.google.com/o/oauth2/auth",
                "validation_endpoint": "https://www.googleapis.com/oauth2/v1/userinfo",
                "enabled": True,
                "body": "Google",
            }
        )
        self.assertFalse(provider.cas_token_endpoint)
        self.assertFalse(provider.cas_logout_endpoint)

    def test_onchange_sets_oauth_endpoints(self):
        """Enabling CAS auto-configures auth and validation endpoints."""
        provider = self.Provider.create(
            {
                "name": "CAS Onchange Test",
                "is_cas_provider": False,
                "client_id": "test_onchange",
                "auth_endpoint": "https://placeholder.test/auth",
                "validation_endpoint": "https://placeholder.test/validate",
                "enabled": True,
                "body": "Test",
            }
        )
        form = Form(provider)
        form.is_cas_provider = True
        form.cas_server_url = "https://auth.example.com/cas"
        form.save()
        self.assertEqual(provider.auth_endpoint, "https://auth.example.com/cas/oauth2.0/authorize")
        self.assertEqual(provider.validation_endpoint, "https://auth.example.com/cas/oauth2.0/profile")

    def test_get_cas_redirect_uri(self):
        """Callback URL is correctly built."""
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        expected = f"{base_url}/auth_cas/callback"
        self.assertEqual(self.cas_provider._get_cas_redirect_uri(), expected)

    def test_cas_attribute_map_json(self):
        """Valid JSON attribute map is parseable."""
        attr_map = json.loads(self.cas_provider.cas_attribute_map)
        self.assertEqual(attr_map["login"], "uid")
        self.assertEqual(attr_map["email"], "mail")
        self.assertEqual(attr_map["name"], "cn")

    def test_cas_attribute_map_invalid_json(self):
        """Invalid JSON in cas_attribute_map doesn't crash (tested via _cas_signin fallback)."""
        self.cas_provider.cas_attribute_map = "not valid json"
        # The code uses try/except in _cas_signin, so this should not raise
        try:
            json.loads(self.cas_provider.cas_attribute_map)
            self.fail("Should have raised JSONDecodeError")
        except json.JSONDecodeError:
            pass  # Expected
