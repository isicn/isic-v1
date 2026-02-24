from odoo import fields, models


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    def _check_access_dms_record(self, operation):
        """Fix: include archived records in access check to allow unarchive."""
        if any(self._ids) and not self.env.su:
            Rule = self.env["ir.rule"]
            domain = Rule._compute_domain(self._name, operation)
            items = self.with_context(active_test=False).search(domain)
            if any(x_id not in items.ids for x_id in self.ids):
                raise Rule._make_access_error(operation, (self - items))

    annee_academique_id = fields.Many2one(
        "isic.annee.academique",
        string="Année académique",
    )
