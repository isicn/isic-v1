from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    matricule = fields.Char(
        string="Matricule",
        index=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("company_id") and not vals.get("company_ids"):
                vals["company_ids"] = [fields.Command.set([vals["company_id"]])]
        return super().create(vals_list)
