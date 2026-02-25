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
        # Fix auth_ldap: exp_authenticate creates env with uid=None. When the
        # avatar SVG is written to ir.attachment, _check_contents calls
        # sudo(False).has_access('write') which fails with "Expected singleton:
        # res.users()" because uid=None resolves to an empty recordset.
        # Fix both the current env AND default_env (used during flush/recompute).
        if not self.env.uid:
            self = self.with_user(SUPERUSER_ID).sudo()
            self.env.transaction.default_env = self.env
        return super().create(vals_list)
