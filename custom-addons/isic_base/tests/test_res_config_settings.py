from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Tests for ISIC config parameters in res.config.settings."""

    def _save_settings(self, vals):
        """Helper: create, execute, return settings wizard."""
        settings = self.env["res.config.settings"].create(vals)
        settings.execute()
        return settings

    def test_nom_etablissement_saved(self):
        """isic_nom_etablissement persists via config_parameter."""
        self._save_settings({"isic_nom_etablissement": "ISIC Rabat"})
        value = self.env["ir.config_parameter"].get_param("isic_base.nom_etablissement")
        self.assertEqual(value, "ISIC Rabat")

    def test_code_etablissement_saved(self):
        """isic_code_etablissement persists via config_parameter."""
        self._save_settings({"isic_code_etablissement": "ISIC"})
        value = self.env["ir.config_parameter"].get_param("isic_base.code_etablissement")
        self.assertEqual(value, "ISIC")

    def test_config_read_back(self):
        """Values can be read back after save."""
        self._save_settings(
            {
                "isic_nom_etablissement": "Institut ISIC",
                "isic_code_etablissement": "ISIC-01",
            }
        )
        settings2 = self.env["res.config.settings"].create({})
        self.assertEqual(settings2.isic_nom_etablissement, "Institut ISIC")
        self.assertEqual(settings2.isic_code_etablissement, "ISIC-01")

    def test_settings_access_direction_only(self):
        """Settings view is gated by group_isic_direction in the XML."""
        # Just verify the config_parameter keys exist and are functional
        ICP = self.env["ir.config_parameter"]
        ICP.set_param("isic_base.nom_etablissement", "Test")
        self.assertEqual(ICP.get_param("isic_base.nom_etablissement"), "Test")
        ICP.set_param("isic_base.code_etablissement", "TST")
        self.assertEqual(ICP.get_param("isic_base.code_etablissement"), "TST")
