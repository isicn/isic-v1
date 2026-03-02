{
    "name": "ISIC - Portail Etudiant",
    "summary": "Portail self-service pour les etudiants ISIC",
    "version": "19.0.1.0.0",
    "category": "Education",
    "author": "ISIC Rabat",
    "website": "https://isic.ac.ma",
    "license": "Other proprietary",
    "depends": ["isic_base", "isic_ged", "isic_approbation", "portal"],
    "post_init_hook": "_post_init_hook",
    "data": [
        "security/isic_portal_security.xml",
        "security/ir.model.access.csv",
        "views/portal_templates.xml",
        "views/portal_dms_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "isic_portal/static/src/scss/portal.scss",
        ],
    },
    "installable": True,
    "application": False,
}
