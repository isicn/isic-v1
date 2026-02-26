# -*- coding: utf-8 -*-

import json
import logging
import secrets
import urllib.parse
import xml.etree.ElementTree as ET

import requests
from werkzeug.utils import redirect

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.addons.auth_oauth.controllers.main import OAuthLogin, OAuthController
from odoo.addons.web.controllers.session import Session as WebSession

try:
    from odoo.addons.http_routing.controllers.main import SessionWebsite
except ImportError:
    SessionWebsite = None

_logger = logging.getLogger(__name__)


class CASAuthLogin(OAuthLogin):
    """
    Extension du login OAuth pour supporter CAS Protocol.
    Override list_providers() pour les providers CAS.
    """

    def list_providers(self):
        """
        Override pour modifier les paramètres des providers CAS.
        Utilise le protocole CAS classique (pas OAuth2).
        """
        providers = super().list_providers()

        for provider in providers:
            # Vérifier si c'est un provider CAS
            oauth_provider = request.env['auth.oauth.provider'].sudo().browse(provider['id'])

            if oauth_provider.is_cas_provider:
                # Construire l'URL de login CAS avec le service callback
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                service_url = f"{base_url}/auth_cas/callback"

                # URL CAS pour le navigateur (auth_endpoint est l'URL publique)
                # cas_server_url est réservé pour les appels serveur-à-serveur
                cas_login_url = oauth_provider.auth_endpoint or oauth_provider.cas_server_url
                if not cas_login_url.endswith('/login'):
                    # Extraire la base CAS depuis auth_endpoint (enlever /oauth2.0/authorize, etc.)
                    for suffix in ('/oauth2.0/authorize', '/oauth2.0', '/p3/serviceValidate'):
                        if suffix in cas_login_url:
                            cas_login_url = cas_login_url.split(suffix)[0]
                            break
                    cas_login_url = cas_login_url.rstrip('/') + '/login'

                # Stocker le provider_id dans la session
                request.session['cas_provider_id'] = provider['id']

                # Construire l'URL d'authentification CAS
                auth_link = f"{cas_login_url}?service={urllib.parse.quote(service_url, safe='')}"
                provider['auth_link'] = auth_link

                _logger.debug("CAS auth link for provider %s: %s", provider['id'], auth_link)

        return providers


class CASAuthController(http.Controller):
    """
    Contrôleur pour le callback CAS Protocol (ticket-based).
    Valide le ticket auprès du serveur CAS.
    """

    @http.route('/auth_cas/callback', type='http', auth='none', csrf=False)
    def cas_callback(self, **kw):
        """
        Callback CAS - reçoit le ticket et le valide auprès du serveur CAS.
        """
        _logger.info("CAS callback received with params: %s", list(kw.keys()))

        # Récupérer le ticket
        ticket = kw.get('ticket')

        if not ticket:
            _logger.error("CAS callback missing ticket")
            return request.redirect('/web/login?oauth_error=missing_ticket')

        # Récupérer le provider
        provider_id = request.session.get('cas_provider_id')
        if not provider_id:
            # Essayer de trouver le provider CAS par défaut
            provider = request.env['auth.oauth.provider'].sudo().search([
                ('is_cas_provider', '=', True),
                ('enabled', '=', True)
            ], limit=1)
            if provider:
                provider_id = provider.id
            else:
                _logger.error("CAS callback: no CAS provider found")
                return request.redirect('/web/login?oauth_error=missing_provider')

        provider = request.env['auth.oauth.provider'].sudo().browse(provider_id)
        if not provider.exists():
            _logger.error("Invalid CAS provider: %s", provider_id)
            return request.redirect('/web/login?oauth_error=invalid_provider')

        try:
            # Valider le ticket auprès du serveur CAS
            user_info = self._validate_cas_ticket(provider, ticket)

            if not user_info:
                _logger.error("CAS ticket validation failed")
                return request.redirect('/web/login?oauth_error=invalid_ticket')

            _logger.info("CAS user authenticated: %s", user_info.get('user') or user_info.get('uid'))

            # Préparer les données pour le signin OAuth
            # Ajouter un user_id pour la compatibilité OAuth
            user_info['user_id'] = user_info.get('user') or user_info.get('uid') or user_info.get('username')

            # Authentifier l'utilisateur via le système OAuth standard
            # _auth_oauth_signin retourne le login de l'utilisateur
            login = request.env['res.users'].sudo()._auth_oauth_signin(
                provider.id, user_info, {}
            )

            _logger.info("CAS signin returned login: %s", login)

            # Récupérer l'utilisateur
            user = request.env['res.users'].sudo().search([('login', '=', login)], limit=1)
            if not user:
                _logger.error("User not found after signin: %s", login)
                return request.redirect('/web/login?oauth_error=user_not_found')

            # Authentifier la session - en Odoo 19, on utilise uid directement
            request.session.uid = user.id
            request.session.login = login
            request.session.session_token = user._compute_session_token(request.session.sid)
            request.env['res.users']._update_last_login()

            # Nettoyer la session
            request.session.pop('cas_provider_id', None)

            # Rediriger vers l'application
            _logger.info("CAS authentication successful for user %s, redirecting to /web", login)
            return request.redirect('/web')

        except AccessDenied as e:
            _logger.error("CAS authentication denied: %s", e)
            return request.redirect('/web/login?oauth_error=access_denied')
        except Exception as e:
            _logger.exception("CAS authentication error: %s", e)
            return request.redirect('/web/login?oauth_error=server_error')

    def _validate_cas_ticket(self, provider, ticket):
        """
        Valide le ticket CAS auprès du serveur CAS.
        Supporte CAS 2.0 (serviceValidate) et CAS 3.0 (p3/serviceValidate).
        """
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        service_url = f"{base_url}/auth_cas/callback"

        # Construire l'URL de validation
        cas_server = provider.cas_server_url or provider.auth_endpoint.rsplit('/login', 1)[0]
        cas_server = cas_server.rstrip('/')

        # Essayer CAS 3.0 d'abord (p3/serviceValidate) pour obtenir les attributs
        validate_url = f"{cas_server}/p3/serviceValidate"

        params = {
            'ticket': ticket,
            'service': service_url,
            'format': 'JSON',  # Demander JSON si supporté
        }

        _logger.debug("Validating CAS ticket at: %s", validate_url)

        try:
            response = requests.get(validate_url, params=params, timeout=30)
            _logger.debug("CAS validation response status: %s", response.status_code)

            if response.status_code != 200:
                _logger.error("CAS validation failed with status %s: %s",
                           response.status_code, response.text[:500])
                return None

            # Essayer de parser comme JSON
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return self._parse_cas_json_response(response.json())
            else:
                # Parser comme XML
                return self._parse_cas_xml_response(response.text)

        except requests.RequestException as e:
            _logger.error("CAS validation request failed: %s", e)
            return None

    def _parse_cas_json_response(self, data):
        """
        Parse la réponse JSON de CAS.
        """
        _logger.debug("Parsing CAS JSON response: %s", data)

        service_response = data.get('serviceResponse', data)

        if 'authenticationSuccess' in service_response:
            success = service_response['authenticationSuccess']
            user_info = {
                'user': success.get('user'),
                'uid': success.get('user'),
            }

            # Ajouter les attributs
            if 'attributes' in success:
                user_info.update(success['attributes'])

            return user_info

        if 'authenticationFailure' in service_response:
            failure = service_response['authenticationFailure']
            _logger.error("CAS authentication failure: %s - %s",
                         failure.get('code'), failure.get('description'))
            return None

        _logger.error("Unknown CAS JSON response format: %s", data)
        return None

    def _parse_cas_xml_response(self, xml_text):
        """
        Parse la réponse XML de CAS.
        """
        _logger.debug("Parsing CAS XML response: %s", xml_text[:500])

        try:
            # Namespace CAS
            ns = {'cas': 'http://www.yale.edu/tp/cas'}

            root = ET.fromstring(xml_text)

            # Chercher authenticationSuccess
            success = root.find('.//cas:authenticationSuccess', ns)
            if success is not None:
                user_elem = success.find('cas:user', ns)
                if user_elem is not None:
                    user_info = {
                        'user': user_elem.text,
                        'uid': user_elem.text,
                    }

                    # Extraire les attributs
                    attributes = success.find('cas:attributes', ns)
                    if attributes is not None:
                        for attr in attributes:
                            # Enlever le namespace du tag
                            tag = attr.tag.split('}')[-1] if '}' in attr.tag else attr.tag
                            user_info[tag] = attr.text

                    _logger.info("CAS XML parsed successfully for user: %s", user_info['user'])
                    return user_info

            # Chercher authenticationFailure
            failure = root.find('.//cas:authenticationFailure', ns)
            if failure is not None:
                code = failure.get('code', 'UNKNOWN')
                _logger.error("CAS authentication failure: %s - %s", code, failure.text)
                return None

            _logger.error("Unknown CAS XML response format")
            return None

        except ET.ParseError as e:
            _logger.error("Failed to parse CAS XML response: %s", e)
            return None


# Hériter du contrôleur le plus spécifique disponible :
# SessionWebsite (http_routing/website) > Session (web)
_LogoutBase = SessionWebsite or WebSession


class CASLogoutController(_LogoutBase):
    """
    Override du contrôleur Session/SessionWebsite pour supporter le SLO CAS.
    Hérite de SessionWebsite quand website est installé, sinon de Session.
    """

    @http.route('/web/session/logout', type='http', auth='none', website=True,
                multilang=False, sitemap=False, readonly=True)
    def logout(self, redirect='/odoo'):
        """
        Override du logout pour supporter le SLO CAS.

        IMPORTANT: L'ordre des opérations est critique !
        On doit récupérer les infos du provider AVANT de détruire la session,
        sinon request.env.user devient Anonymous et on perd le provider.
        """
        # 1. AVANT le logout : récupérer les infos du provider CAS
        cas_logout_url = None
        uid = request.session.uid
        if uid:
            try:
                slo_enabled = request.env['ir.config_parameter'].sudo().get_param(
                    'auth_cas.slo_enabled', 'True'
                )
                user = request.env['res.users'].sudo().browse(uid)
                provider = user.oauth_provider_id

                if slo_enabled == 'True' and provider and provider.is_cas_provider:
                    # 2. Construire l'URL de logout CAS
                    logout_endpoint = provider.cas_logout_endpoint

                    if not logout_endpoint:
                        # Fallback: extraire la base CAS depuis cas_server_url ou auth_endpoint
                        cas_server = provider.cas_server_url
                        if not cas_server and provider.auth_endpoint:
                            endpoint = provider.auth_endpoint
                            for suffix in ('/oauth2.0/authorize', '/oauth2.0', '/login'):
                                if suffix in endpoint:
                                    cas_server = endpoint.split(suffix)[0]
                                    break
                        if cas_server:
                            logout_endpoint = cas_server.rstrip('/') + '/logout'

                    if logout_endpoint:
                        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        service_url = base_url + redirect
                        cas_logout_url = f"{logout_endpoint}?service={urllib.parse.quote(service_url, safe='')}"
                        _logger.info("CAS SLO will redirect to: %s", cas_logout_url)
            except Exception as e:
                _logger.warning("Error building CAS logout URL: %s", e)

        # 3. Terminer la session Odoo (appel au parent)
        request.session.logout(keep_db=True)

        # 4. Rediriger vers CAS (URL externe → local=False) ou fallback standard
        if cas_logout_url:
            return request.redirect(cas_logout_url, local=False)

        return request.redirect(redirect, 303)
