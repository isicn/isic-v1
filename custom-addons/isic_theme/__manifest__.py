{
    "name": "ISIC Theme",
    "summary": "ISIC institutional branding for Odoo backend",
    "version": "19.0.1.2.0",
    "category": "Hidden",
    "author": "ISIC Rabat",
    "website": "https://isic.ac.ma",
    "license": "Other proprietary",
    "depends": ["web", "website", "muk_web_theme"],
    "data": [
        "views/webclient_templates.xml",
        "views/res_users_views.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            (
                "after",
                "muk_web_colors/static/src/scss/colors_light.scss",
                "isic_theme/static/src/scss/primary_variables.scss",
            ),
        ],
        "web.assets_backend": [
            "isic_theme/static/src/scss/backend.scss",
            "isic_theme/static/src/scss/print.scss",
            "isic_theme/static/src/scss/rtl.scss",
            "isic_theme/static/src/css/has_rules.css",
            "isic_theme/static/src/js/dms_store_fix.js",
            "isic_theme/static/src/js/hide_tier_review_menu.js",
            "isic_theme/static/src/xml/chatter.xml",
        ],
        "web.assets_frontend": [
            "isic_theme/static/src/scss/backend.scss",
            "isic_theme/static/src/scss/login.scss",
            "isic_theme/static/src/scss/rtl.scss",
        ],
        "web.assets_web_dark": [
            (
                "after",
                "muk_web_colors/static/src/scss/colors_dark.scss",
                "isic_theme/static/src/scss/primary_variables_dark.scss",
            ),
            "isic_theme/static/src/scss/dark.scss",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "auto_install": False,
    "application": False,
}
