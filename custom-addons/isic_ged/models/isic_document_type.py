from odoo import fields, models


class IsicDocumentType(models.Model):
    _name = "isic.document.type"
    _description = "Type de document"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    validation_required = fields.Boolean(
        string="Validation requise",
        default=False,
        help="Ce type de document nécessite une validation avant archivage.",
    )
    retention_days = fields.Integer(
        string="Conservation (jours)",
        help="Durée de conservation en jours. 0 = illimitée.",
    )
    sequence = fields.Integer(default=10)

    _unique_code = models.Constraint(
        "UNIQUE(code)",
        "Le code du type de document doit être unique.",
    )
