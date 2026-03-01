{
    "name": "ISIC - GED",
    "summary": "Gestion électronique des documents ISIC",
    "version": "19.0.2.0.0",
    "category": "Education",
    "author": "ISIC Rabat",
    "website": "https://isic.ac.ma",
    "license": "Other proprietary",
    "depends": ["isic_base", "dms", "dms_field"],
    "external_dependencies": {
        "python": ["pypdf", "docx", "openpyxl"],
    },
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/isic_document_type_data.xml",
        "data/isic_dms_data.xml",
        "data/isic_ged_server_actions.xml",
        "data/isic_classification_rules_data.xml",
        "views/dms_file_views.xml",
        "views/dms_directory_views.xml",
        "views/isic_document_type_views.xml",
        "views/isic_document_version_views.xml",
        "views/isic_classification_rule_views.xml",
    ],
    "demo": [
        "demo/isic_ged_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "isic_ged/static/src/scss/kanban.scss",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": True,
}
