{
    "name": "ISIC Theme",
    "summary": "ISIC institutional branding for Odoo backend",
    "version": "19.0.1.0.0",
    "category": "Hidden",
    "author": "ISIC Rabat",
    "website": "https://isic.ac.ma",
    "license": "Other proprietary",
    "depends": ["web"],
    "data": [
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            (
                "prepend",
                "isic_theme/static/src/scss/primary_variables.scss",
            ),
        ],
        "web.assets_backend": [
            "isic_theme/static/src/scss/backend.scss",
        ],
        "web.assets_frontend": [
            "isic_theme/static/src/scss/backend.scss",
            "isic_theme/static/src/scss/login.scss",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "auto_install": False,
    "application": False,
}
