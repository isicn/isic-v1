{
    "name": "ISIC - Portail",
    "summary": "Portail intranet ISIC avec dashboards par profil et accès rapide aux modules",
    "version": "19.0.1.0.0",
    "category": "Education",
    "author": "ISIC Rabat",
    "website": "https://isic.ac.ma",
    "license": "Other proprietary",
    "depends": ["isic_base", "isic_ged", "isic_approbation"],
    "data": [
        "views/isic_portal_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "isic_portal/static/src/dashboard/**/*",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": True,
}
