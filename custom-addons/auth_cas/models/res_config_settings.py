from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Settings CAS dans la configuration générale"""

    _inherit = "res.config.settings"

    # CAS Settings
    cas_enabled = fields.Boolean(
        string="Enable CAS SSO", config_parameter="auth_cas.enabled", help="Activer l'authentification CAS SSO"
    )

    cas_server_url = fields.Char(
        string="CAS Server URL",
        config_parameter="auth_cas.server_url",
        help="URL du serveur CAS (ex: https://cas.isic.ma/cas)",
    )

    cas_client_id = fields.Char(
        string="CAS Client ID",
        config_parameter="auth_cas.client_id",
        help="Client ID OAuth2 enregistré sur le serveur CAS",
    )

    cas_client_secret = fields.Char(
        string="CAS Client Secret", config_parameter="auth_cas.client_secret", help="Client Secret OAuth2"
    )

    cas_callback_url = fields.Char(
        string="Callback URL",
        compute="_compute_cas_callback_url",
        help="URL de callback à configurer sur le serveur CAS",
    )

    cas_auto_create_users = fields.Boolean(
        string="Auto-create Users",
        config_parameter="auth_cas.auto_create_users",
        default=True,
        help="Créer automatiquement les utilisateurs lors de leur première connexion CAS",
    )

    cas_sync_groups = fields.Boolean(
        string="Sync Groups on Login",
        config_parameter="auth_cas.sync_groups",
        default=True,
        help="Synchroniser les groupes ISIC à chaque connexion CAS",
    )

    cas_slo_enabled = fields.Boolean(
        string="Enable Single Logout (SLO)",
        config_parameter="auth_cas.slo_enabled",
        default=True,
        help="Activer le Single Logout - déconnexion du CAS lors du logout Odoo",
    )

    cas_provider_id = fields.Many2one(
        "auth.oauth.provider",
        string="CAS OAuth Provider",
        compute="_compute_cas_provider",
        help="Provider OAuth configuré pour CAS",
    )

    # LDAP Settings (raccourcis)
    ldap_enabled = fields.Boolean(
        string="LDAP Enabled", compute="_compute_ldap_enabled", help="Indique si l'authentification LDAP est configurée"
    )

    ldap_server_count = fields.Integer(
        string="LDAP Servers", compute="_compute_ldap_enabled", help="Nombre de serveurs LDAP configurés"
    )

    @api.depends_context("company")
    def _compute_cas_callback_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            record.cas_callback_url = f"{base_url}/auth_cas/callback"

    @api.depends("cas_server_url", "cas_client_id")
    def _compute_cas_provider(self):
        for record in self:
            provider = self.env["auth.oauth.provider"].search(
                [("is_cas_provider", "=", True), ("enabled", "=", True)], limit=1
            )
            record.cas_provider_id = provider.id if provider else False

    def _compute_ldap_enabled(self):
        for record in self:
            ldap_servers = self.env["res.company.ldap"].search_count([("company", "=", self.env.company.id)])
            record.ldap_server_count = ldap_servers
            record.ldap_enabled = ldap_servers > 0

    def action_configure_cas_provider(self):
        """Configure ou ouvre le provider CAS"""
        self.ensure_one()

        # Chercher ou créer le provider CAS
        provider = self.env["auth.oauth.provider"].search([("is_cas_provider", "=", True)], limit=1)

        if not provider:
            # Créer un nouveau provider
            cas_base = (self.cas_server_url or "").rstrip("/")
            provider = self.env["auth.oauth.provider"].create(
                {
                    "name": "ISIC CAS",
                    "is_cas_provider": True,
                    "cas_server_url": cas_base,
                    "auth_endpoint": f"{cas_base}/oauth2.0/authorize" if cas_base else "",
                    "validation_endpoint": f"{cas_base}/oauth2.0/profile" if cas_base else "",
                    "client_id": self.cas_client_id or "",
                    "client_secret": self.cas_client_secret or "",
                    "enabled": self.cas_enabled,
                    "body": "Se connecter avec CAS ISIC",
                    "css_class": "fa fa-fw fa-university",
                }
            )

        return {
            "type": "ir.actions.act_window",
            "res_model": "auth.oauth.provider",
            "res_id": provider.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_cas_mappings(self):
        """Ouvre la vue des mappings CAS -> Groupes"""
        return {
            "type": "ir.actions.act_window",
            "name": "CAS Group Mappings",
            "res_model": "auth.cas.group.mapping",
            "view_mode": "tree,form",
            "target": "current",
        }

    def action_open_ldap_config(self):
        """Ouvre la configuration LDAP"""
        return {
            "type": "ir.actions.act_window",
            "name": "LDAP Configuration",
            "res_model": "res.company.ldap",
            "view_mode": "tree,form",
            "domain": [("company", "=", self.env.company.id)],
            "context": {"default_company": self.env.company.id},
            "target": "current",
        }

    @api.model
    def get_values(self):
        res = super().get_values()
        # Les valeurs sont récupérées via config_parameter automatiquement
        return res

    def set_values(self):
        super().set_values()

        # Mettre à jour le provider CAS si nécessaire
        if self.cas_enabled and self.cas_server_url:
            provider = self.env["auth.oauth.provider"].search([("is_cas_provider", "=", True)], limit=1)

            if provider:
                provider.write(
                    {
                        "cas_server_url": self.cas_server_url,
                        "client_id": self.cas_client_id,
                        "client_secret": self.cas_client_secret,
                        "enabled": self.cas_enabled,
                    }
                )
