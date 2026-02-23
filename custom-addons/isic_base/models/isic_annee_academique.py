from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IsicAnneeAcademique(models.Model):
    _name = "isic.annee.academique"
    _description = "Année académique"
    _inherit = ["mail.thread"]
    _order = "date_start desc"

    name = fields.Char(
        string="Année académique",
        compute="_compute_name",
        store=True,
        readonly=True,
    )
    code = fields.Char(
        string="Code",
        required=True,
        tracking=True,
        help="Ex : 2025-2026",
    )
    date_start = fields.Date(
        string="Date de début",
        required=True,
        tracking=True,
    )
    date_end = fields.Date(
        string="Date de fin",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("open", "En cours"),
            ("closed", "Clôturée"),
        ],
        string="État",
        default="draft",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    inscription_ouverte = fields.Boolean(
        string="Inscriptions ouvertes",
        default=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Société",
        default=lambda self: self.env.company,
    )

    _unique_code_company = models.Constraint(
        "UNIQUE(code, company_id)",
        "Le code de l'année académique doit être unique par société.",
    )

    @api.depends("code")
    def _compute_name(self):
        for rec in self:
            rec.name = rec.code or ""

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_start >= rec.date_end:
                raise ValidationError("La date de début doit être antérieure à la date de fin.")

    @api.constrains("state")
    def _check_single_open(self):
        for rec in self:
            if rec.state == "open":
                other = self.search(
                    [
                        ("state", "=", "open"),
                        ("company_id", "=", rec.company_id.id),
                        ("id", "!=", rec.id),
                    ]
                )
                if other:
                    raise ValidationError("Une seule année académique peut être en cours par société.")

    def action_ouvrir(self):
        self.write({"state": "open"})

    def action_cloturer(self):
        self.write({"state": "closed", "inscription_ouverte": False})

    def action_reset_draft(self):
        self.write({"state": "draft"})
