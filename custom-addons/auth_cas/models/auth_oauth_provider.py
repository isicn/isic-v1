from odoo import api, fields, models


class AuthOAuthProvider(models.Model):
    """Extension du provider OAuth pour supporter CAS 5.0+"""

    _inherit = "auth.oauth.provider"

    # Champs CAS spécifiques
    is_cas_provider = fields.Boolean(
        string="CAS Provider", default=False, help="Cocher si ce provider est un serveur CAS utilisant OAuth2"
    )

    cas_server_url = fields.Char(
        string="CAS Server URL", help="URL de base du serveur CAS (ex: https://cas.isic.ma/cas)"
    )

    cas_token_endpoint = fields.Char(
        string="Token Endpoint",
        compute="_compute_cas_endpoints",
        store=True,
        help="Endpoint pour échanger le code contre un token",
    )

    cas_logout_endpoint = fields.Char(
        string="Logout Endpoint",
        compute="_compute_cas_endpoints",
        store=True,
        help="Endpoint pour le Single Logout (SLO)",
    )

    client_secret = fields.Char(string="Client Secret", help="Secret OAuth2 fourni par le serveur CAS")

    cas_attribute_map = fields.Text(
        string="Attribute Mapping (JSON)",
        default='{"login": "uid", "email": "mail", "name": "cn"}',
        help="""Mapping JSON des attributs CAS vers les champs Odoo.
Exemple: {"login": "uid", "email": "mail", "name": "cn", "groups": "memberOf"}""",
    )

    cas_use_pkce = fields.Boolean(
        string="Use PKCE", default=False, help="Utiliser PKCE (Proof Key for Code Exchange) pour plus de sécurité"
    )

    cas_scope = fields.Char(
        string="OAuth Scopes", default="openid profile email", help="Scopes OAuth2 à demander au serveur CAS"
    )

    @api.depends("cas_server_url")
    def _compute_cas_endpoints(self):
        """Calcule les endpoints CAS à partir de l'URL de base"""
        for provider in self:
            if provider.cas_server_url and provider.is_cas_provider:
                base = provider.cas_server_url.rstrip("/")
                provider.cas_token_endpoint = f"{base}/oauth2.0/accessToken"
                provider.cas_logout_endpoint = f"{base}/logout"
            else:
                provider.cas_token_endpoint = False
                provider.cas_logout_endpoint = False

    @api.onchange("is_cas_provider", "cas_server_url")
    def _onchange_cas_provider(self):
        """Configure automatiquement les champs OAuth pour CAS"""
        if self.is_cas_provider and self.cas_server_url:
            base = self.cas_server_url.rstrip("/")
            # Authorization endpoint standard CAS OAuth2
            self.auth_endpoint = f"{base}/oauth2.0/authorize"
            # Validation endpoint pour récupérer les infos utilisateur
            self.validation_endpoint = f"{base}/oauth2.0/profile"
            # CAS OAuth2 utilise le flow authorization_code
            # Le scope est géré via cas_scope

    def _get_cas_redirect_uri(self):
        """Retourne l'URI de callback pour ce provider CAS"""
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/auth_cas/callback"
