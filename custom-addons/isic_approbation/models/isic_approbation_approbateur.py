from odoo import api, fields, models


class IsicApprobationApprobateur(models.Model):
    _name = "isic.approbation.approbateur"
    _description = "Approbateur d'une catégorie de demande"
    _order = "sequence"

    categorie_id = fields.Many2one(
        "isic.approbation.categorie",
        string="Catégorie",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Ordre", default=10)
    review_type = fields.Selection(
        [("group", "Groupe"), ("individual", "Utilisateur")],
        string="Type",
        default="group",
        required=True,
    )
    reviewer_group_id = fields.Many2one(
        "res.groups",
        string="Groupe approbateur",
    )
    reviewer_id = fields.Many2one(
        "res.users",
        string="Utilisateur approbateur",
    )
    has_comment = fields.Boolean(string="Commentaire", default=True)
    tier_definition_id = fields.Many2one(
        "tier.definition",
        string="Circuit lié",
        readonly=True,
        ondelete="set null",
    )
    name = fields.Char(string="Nom", compute="_compute_name")

    @api.depends("review_type", "reviewer_group_id", "reviewer_id")
    def _compute_name(self):
        for rec in self:
            if rec.review_type == "group" and rec.reviewer_group_id:
                rec.name = rec.reviewer_group_id.name
            elif rec.review_type == "individual" and rec.reviewer_id:
                rec.name = rec.reviewer_id.name
            else:
                rec.name = ""

    def unlink(self):
        tiers = self.mapped("tier_definition_id")
        res = super().unlink()
        tiers.exists().unlink()
        return res
