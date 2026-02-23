from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    matricule = fields.Char(
        string="Matricule",
        index=True,
        copy=False,
    )
