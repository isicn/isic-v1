{
    "name": "ISIC - Dashboard",
    "summary": "Tableau de bord ISIC avec sections configurables par role",
    "version": "19.0.1.0.0",
    "category": "Education",
    "author": "ISIC Rabat",
    "website": "https://isic.ac.ma",
    "license": "Other proprietary",
    "depends": ["isic_base", "isic_ged", "isic_approbation"],
    "data": [
        "security/ir.model.access.csv",
        "data/isic_dashboard_section_data.xml",
        "views/isic_dashboard_section_views.xml",
        "views/isic_dashboard_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "isic_dashboard/static/src/dashboard/**/*",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": True,
}
