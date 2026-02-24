{
    "name": "ISIC Theme - Website Bridge",
    "summary": "Applique le design ISIC sur la page login quand le module website est installé",
    "version": "19.0.1.0.0",
    "category": "Website",
    "author": "ISIC Rabat",
    "website": "https://isic.ac.ma",
    "license": "Other proprietary",
    "depends": ["isic_theme", "website"],
    "data": [
        "views/login_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "isic_theme_website/static/src/scss/login.scss",
        ],
    },
    "auto_install": True,
    "installable": True,
}
