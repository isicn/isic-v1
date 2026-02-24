from odoo import fields, models


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    annee_academique_id = fields.Many2one(
        "isic.annee.academique",
        string="Année académique",
    )
