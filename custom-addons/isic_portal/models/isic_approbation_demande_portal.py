from odoo import models


class IsicApprobationDemandePortal(models.Model):
    _name = "isic.approbation.demande"
    _inherit = ["isic.approbation.demande", "portal.mixin"]

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = f"/my/demandes/{rec.id}"
