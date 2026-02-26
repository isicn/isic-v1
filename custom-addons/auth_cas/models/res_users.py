# -*- coding: utf-8 -*-

import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Extension de res.users pour le support CAS"""
    _inherit = 'res.users'

    cas_uid = fields.Char(
        string='CAS UID',
        help="Identifiant unique de l'utilisateur dans le CAS"
    )

    cas_last_sync = fields.Datetime(
        string='Last CAS Sync',
        help="Dernière synchronisation des attributs CAS"
    )

    cas_attributes = fields.Text(
        string='CAS Attributes (JSON)',
        help="Derniers attributs reçus du CAS (pour debug)"
    )

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """
        Override pour supporter l'authentification CAS.
        Si le provider est un CAS provider, utilise la logique CAS.
        Sinon, délègue au comportement standard OAuth.
        """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)

        if oauth_provider.is_cas_provider:
            return self._cas_signin(oauth_provider, validation, params)

        # Comportement standard OAuth
        return super()._auth_oauth_signin(provider, validation, params)

    def _cas_signin(self, provider, validation, params):
        """
        Logique d'authentification CAS.

        :param provider: auth.oauth.provider record
        :param validation: dict des données de validation (attributs CAS)
        :param params: dict des paramètres OAuth
        :return: login de l'utilisateur
        """
        _logger.debug("CAS signin validation data: %s", validation)

        # Parser le mapping d'attributs
        try:
            attr_map = json.loads(provider.cas_attribute_map or '{}')
        except json.JSONDecodeError:
            attr_map = {'login': 'uid', 'email': 'mail', 'name': 'cn'}

        # Extraire les infos utilisateur selon le mapping
        # Le protocole CAS classique retourne 'user' ou 'uid'
        cas_uid = (
            validation.get('user') or
            validation.get('user_id') or
            validation.get('uid') or
            validation.get('username') or
            validation.get(attr_map.get('login', 'uid')) or
            validation.get('id')
        )

        email_raw = (
            validation.get('mail') or
            validation.get('email') or
            validation.get(attr_map.get('email', 'mail'), '')
        )
        # Gérer le cas où l'email est une liste (CAS retourne parfois des listes)
        email = email_raw[0] if isinstance(email_raw, list) else email_raw

        name_raw = (
            validation.get('cn') or
            validation.get('displayName') or
            validation.get('name') or
            validation.get(attr_map.get('name', 'cn'), cas_uid)
        )
        # Gérer le cas où le nom est une liste
        name = name_raw[0] if isinstance(name_raw, list) else name_raw

        if not cas_uid:
            _logger.error("CAS validation missing UID: %s", validation)
            raise AccessDenied(_("CAS authentication failed: no user identifier"))

        _logger.info("CAS signin for user: %s (email: %s)", cas_uid, email)

        # Chercher l'utilisateur existant
        user = self.search([
            ('oauth_provider_id', '=', provider.id),
            '|',
            ('oauth_uid', '=', cas_uid),
            ('cas_uid', '=', cas_uid),
        ], limit=1)

        if not user:
            # Chercher par login = cas_uid (cas le plus courant)
            user = self.search([('login', '=', cas_uid)], limit=1)

        if not user and email:
            # Chercher par login = email ou email = email
            user = self.search([('login', '=', email)], limit=1)
            if not user:
                user = self.search([('email', '=', email)], limit=1)

        if user:
            # Utilisateur existant - mise à jour
            user._cas_update_user(provider, validation, cas_uid)
            return user.login
        else:
            # Nouvel utilisateur - création
            return self._cas_create_user(
                provider, validation, cas_uid, email, name
            )

    def _cas_create_user(self, provider, validation, cas_uid, email, name):
        """
        Crée un nouvel utilisateur à partir des attributs CAS.

        :return: login du nouvel utilisateur
        """
        # Résoudre les groupes depuis les attributs CAS
        CASMapping = self.env['auth.cas.group.mapping']
        group_ids, is_internal = CASMapping.resolve_groups_from_cas(validation, provider.id)

        # Déterminer le login - utiliser le CAS UID si pas d'email
        login = cas_uid  # Utiliser l'identifiant CAS comme login

        # Gérer le cas où le login est une liste
        if isinstance(login, list):
            login = login[0] if login else cas_uid
        if isinstance(email, list):
            email = email[0] if email else ''
        if isinstance(name, list):
            name = name[0] if name else login

        _logger.info("Creating CAS user: login=%s, name=%s, email=%s, is_internal=%s",
                    login, name, email, is_internal)

        try:
            # Obtenir la company par défaut
            company = self.env['res.company'].sudo().search([], limit=1)

            # Préparer les valeurs de base
            # Ne pas passer partner_id : Odoo le crée automatiquement
            vals = {
                'name': name or login,
                'login': login,
                'email': email or '',
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
                'oauth_provider_id': provider.id,
                'oauth_uid': cas_uid,
                'cas_uid': cas_uid,
                'cas_attributes': json.dumps(validation, default=str),
                'cas_last_sync': fields.Datetime.now(),
                'active': True,
            }

            # Créer l'utilisateur
            new_user = self.sudo().with_context(no_reset_password=True).create(vals)

            # Les utilisateurs CAS sont déjà authentifiés via SSO,
            # on leur donne karma=1 pour éviter le message "compte non vérifié"
            if 'karma' in self._fields:
                new_user.sudo().write({'karma': 1})

            # Ajouter les groupes appropriés
            if is_internal and group_ids:
                # Utilisateur interne avec groupes ISIC
                new_user.sudo().write({'group_ids': [(4, gid) for gid in group_ids]})
                _logger.info("CAS internal user created: %s (id=%d) with groups %s",
                           login, new_user.id, group_ids)
            else:
                # Utilisateur portail : remplacer group_user par group_portal
                # (les deux sont exclusifs dans Odoo 19)
                portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
                internal_group = self.env.ref('base.group_user', raise_if_not_found=False)
                if portal_group:
                    group_cmds = []
                    if internal_group and internal_group in new_user.group_ids:
                        group_cmds.append((3, internal_group.id))
                    group_cmds.append((4, portal_group.id))
                    if group_ids:
                        group_cmds.extend([(4, gid) for gid in group_ids])
                    new_user.sudo().write({'group_ids': group_cmds})
                _logger.info("CAS portal user created: %s (id=%d)", login, new_user.id)

            return new_user.login

        except Exception as e:
            _logger.exception("Failed to create CAS user %s: %s", login, e)
            raise AccessDenied(_("Failed to create user account: %s") % str(e))

    def _cas_create_partner(self, login, name, email):
        """
        Crée ou trouve un partner pour un nouvel utilisateur CAS.
        """
        Partner = self.env['res.partner'].sudo()

        # Chercher un partner existant par email
        partner = None
        if email:
            partner = Partner.search([('email', '=', email)], limit=1)

        if not partner:
            partner = Partner.create({
                'name': name or login,
                'email': email or '',
            })
            _logger.info("Created partner for CAS user: %s", partner.name)

        return partner

    def _cas_update_user(self, provider, validation, cas_uid):
        """
        Met à jour un utilisateur existant avec les données CAS.
        """
        self.ensure_one()

        # Résoudre les groupes
        CASMapping = self.env['auth.cas.group.mapping']
        group_ids, is_internal = CASMapping.resolve_groups_from_cas(validation, provider.id)

        vals = {
            'oauth_provider_id': provider.id,
            'oauth_uid': cas_uid,
            'oauth_access_token': validation.get('access_token', ''),
            'cas_uid': cas_uid,
            'cas_attributes': json.dumps(validation),
            'cas_last_sync': fields.Datetime.now(),
        }

        # Récupérer les groupes ISIC actuels via leurs XML IDs
        isic_group_refs = [
            'isic_base.group_isic_etudiant',
            'isic_base.group_isic_enseignant',
            'isic_base.group_isic_responsable_filiere',
            'isic_base.group_isic_departement',
            'isic_base.group_isic_scolarite',
            'isic_base.group_isic_stages',
            'isic_base.group_isic_bibliotheque',
            'isic_base.group_isic_financier',
            'isic_base.group_isic_technique',
            'isic_base.group_isic_cooperation',
            'isic_base.group_isic_recherche',
            'isic_base.group_isic_admin_scolarite',
            'isic_base.group_isic_da_pedagogie',
            'isic_base.group_isic_da_stages',
            'isic_base.group_isic_secretariat',
            'isic_base.group_isic_direction',
        ]
        isic_groups = self.env['res.groups']
        for ref in isic_group_refs:
            group = self.env.ref(ref, raise_if_not_found=False)
            if group:
                isic_groups |= group

        if is_internal and group_ids:
            # Utilisateur interne avec groupes ISIC spécifiques
            current_non_isic = self.group_ids - isic_groups
            new_groups = current_non_isic | self.env['res.groups'].browse(group_ids)
            vals['group_ids'] = [(6, 0, new_groups.ids)]
            _logger.info("CAS user %s updated as internal with groups %s", self.login, group_ids)
        else:
            # Pas de mapping interne -> utilisateur portail
            # Retirer tous les groupes internes et ISIC, assigner portail
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
            internal_group = self.env.ref('base.group_user', raise_if_not_found=False)
            if portal_group:
                # Retirer les groupes ISIC et le groupe interne
                groups_to_remove = isic_groups
                if internal_group:
                    groups_to_remove |= internal_group
                current_clean = self.group_ids - groups_to_remove
                new_groups = current_clean | portal_group
                # Ajouter les groupes ISIC non-internes (ex: étudiant)
                if group_ids:
                    new_groups |= self.env['res.groups'].browse(group_ids)
                vals['group_ids'] = [(6, 0, new_groups.ids)]
            _logger.info("CAS user %s updated as portal", self.login)

        self.sudo().write(vals)
        _logger.info("CAS user updated: %s", self.login)

    @api.model
    def _cas_resolve_groups(self, cas_attributes, provider_id=None):
        """
        Résout les groupes Odoo à partir des attributs CAS.
        Wrapper pour faciliter l'appel depuis les controllers.
        """
        return self.env['auth.cas.group.mapping'].resolve_groups_from_cas(
            cas_attributes, provider_id
        )
