from odoo import api, fields, models
from odoo.exceptions import UserError


class DmsFile(models.Model):
    _inherit = "dms.file"

    def _check_access_dms_record(self, operation):
        """Fix: include archived records in access check to allow unarchive."""
        if any(self._ids) and not self.env.su:
            Rule = self.env["ir.rule"]
            domain = Rule._compute_domain(self._name, operation)
            items = self.with_context(active_test=False).search(domain)
            if any(x_id not in items.ids for x_id in self.ids):
                raise Rule._make_access_error(operation, (self - items))

    document_type_id = fields.Many2one(
        "isic.document.type",
        string="Type de document",
        tracking=True,
    )
    ged_state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("validated", "Validé"),
            ("archived", "Archivé"),
        ],
        string="État GED",
        default="draft",
        tracking=True,
    )
    reference = fields.Char(
        string="Référence",
        index=True,
        copy=False,
        tracking=True,
    )
    date_document = fields.Date(
        string="Date du document",
        tracking=True,
    )
    annee_academique_id = fields.Many2one(
        "isic.annee.academique",
        string="Année académique",
        tracking=True,
    )
    valideur_id = fields.Many2one(
        "res.users",
        string="Validé par",
        readonly=True,
    )
    date_validation = fields.Datetime(
        string="Date de validation",
        readonly=True,
    )

    def action_validate(self):
        for rec in self:
            if rec.ged_state != "draft":
                raise UserError("Seul un document en brouillon peut être validé.")
            rec.write(
                {
                    "ged_state": "validated",
                    "valideur_id": self.env.uid,
                    "date_validation": fields.Datetime.now(),
                }
            )

    def action_archive_ged(self):
        for rec in self:
            if rec.document_type_id.validation_required and rec.ged_state != "validated":
                raise UserError("Ce type de document nécessite une validation avant archivage.")
            rec.write({"ged_state": "archived"})

    def action_reset_draft(self):
        self.write({"ged_state": "draft", "valideur_id": False, "date_validation": False})

    @api.onchange("document_type_id")
    def _onchange_document_type_id(self):
        if self.document_type_id and not self.annee_academique_id:
            self.annee_academique_id = self.env["isic.annee.academique"]._get_current()
