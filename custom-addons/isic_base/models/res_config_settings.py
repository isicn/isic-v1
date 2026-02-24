from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    isic_nom_etablissement = fields.Char(
        string="Nom de l'établissement",
        config_parameter="isic_base.nom_etablissement",
    )
    isic_code_etablissement = fields.Char(
        string="Code établissement",
        config_parameter="isic_base.code_etablissement",
    )
