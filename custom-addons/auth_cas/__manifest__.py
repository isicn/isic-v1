# -*- coding: utf-8 -*-
{
    'name': 'ISIC CAS SSO Authentication',
    'version': '19.0.1.0.0',
    'category': 'Hidden/Tools',
    'summary': 'Authentification CAS SSO avec support LDAP pour ISIC',
    'description': """
ISIC CAS SSO Authentication
===========================

Ce module fournit l'authentification Single Sign-On (SSO) via CAS 5.0+
avec OAuth2 pour l'Institut Supérieur de l'Information et de la Communication.

Fonctionnalités:
----------------
* Intégration CAS 5.0+ via OAuth2 (authorization code flow)
* Support LDAP comme backend d'authentification de fallback
* Mapping automatique des attributs CAS vers les groupes ISIC
* Provisionnement automatique des utilisateurs
* Single Logout (SLO)
* Configuration via l'interface Odoo

Architecture:
-------------
[Navigateur] -> [CAS Server] -> [LDAP]
                    |
                    v (OAuth2)
              [Odoo + auth_cas]
    """,
    'author': 'ISIC',
    'website': 'https://isic.ma',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'base_setup',
        'web',
        'http_routing',
        'auth_oauth',
        'auth_ldap',
        'isic_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/auth_cas_provider_data.xml',
        'data/cas_group_mapping_data.xml',
        'views/res_config_settings_views.xml',
        'views/cas_group_mapping_views.xml',
        'views/auth_oauth_provider_views.xml',
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'auth_cas/static/src/scss/auth_cas.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
