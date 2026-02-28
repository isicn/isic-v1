from odoo import fields, models


class IsicDashboardSection(models.Model):
    _name = "isic.dashboard.section"
    _description = "Section du tableau de bord"
    _order = "sequence, id"

    name = fields.Char(
        string="Nom",
        required=True,
        translate=True,
    )
    code = fields.Char(
        string="Code technique",
        required=True,
        help="Identifiant unique lié à la méthode Python _section_{code}().",
    )
    icon = fields.Char(
        string="Icône",
        default="fa-th-large",
        help="Classe FontAwesome (ex : fa-tachometer).",
    )
    sequence = fields.Integer(
        string="Ordre",
        default=10,
    )
    group_ids = fields.Many2many(
        "res.groups",
        string="Groupes autorisés",
        help="Laissez vide pour afficher à tous les utilisateurs internes.",
    )
    active = fields.Boolean(
        string="Publié",
        default=True,
    )
    has_chart = fields.Boolean(
        string="Graphiques",
        default=False,
        help="Appelle aussi _chart_{code}() pour afficher des graphiques.",
    )
    description = fields.Text(
        string="Description",
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "Le code technique doit être unique."),
    ]
