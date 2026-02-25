from odoo import api, fields, models, SUPERUSER_ID


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
        # When called via sudo() (e.g. auth_ldap), ensure env.uid is a valid user.
        # Otherwise sudo(False) inside ir.attachment._check_contents fails with
        # "Expected singleton: res.users()" because env.uid has no matching record.
        if self.env.su and not self.env.uid:
            self = self.with_user(SUPERUSER_ID).sudo()
        return super().create(vals_list)
