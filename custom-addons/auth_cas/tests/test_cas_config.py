from .common import CASTestCase


class TestCASConfig(CASTestCase):
    """Tests for CAS configuration settings."""

    def _save_settings(self, vals):
        """Helper: create, execute, return settings wizard."""
        settings = self.env["res.config.settings"].create(vals)
        settings.execute()
        return settings

    def test_config_parameters_saved(self):
        """CAS config parameters are persisted via ir.config_parameter."""
        self._save_settings(
            {
                "cas_enabled": True,
                "cas_server_url": "https://cas.isic.ma/cas",
                "cas_client_id": "odoo_prod",
                "cas_client_secret": "secret123",
            }
        )
        ICP = self.env["ir.config_parameter"].sudo()
        self.assertEqual(ICP.get_param("auth_cas.enabled"), "True")
        self.assertEqual(ICP.get_param("auth_cas.server_url"), "https://cas.isic.ma/cas")
        self.assertEqual(ICP.get_param("auth_cas.client_id"), "odoo_prod")
        self.assertEqual(ICP.get_param("auth_cas.client_secret"), "secret123")

    def test_compute_callback_url(self):
        """Callback URL is correctly computed."""
        settings = self.env["res.config.settings"].create({})
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        self.assertEqual(settings.cas_callback_url, f"{base_url}/auth_cas/callback")

    def test_action_configure_provider_creates(self):
        """action_configure_cas_provider creates provider if none exists."""
        # Deactivate existing provider
        self.cas_provider.is_cas_provider = False
        settings = self.env["res.config.settings"].create(
            {
                "cas_enabled": True,
                "cas_server_url": "https://new.cas.test/cas",
                "cas_client_id": "new_client",
            }
        )
        action = settings.action_configure_cas_provider()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "auth.oauth.provider")
        provider = self.env["auth.oauth.provider"].browse(action["res_id"])
        self.assertTrue(provider.is_cas_provider)
        self.assertEqual(provider.name, "ISIC CAS")
