import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IsicApprobationDemande(models.Model):
    _name = "isic.approbation.demande"
    _description = "Demande d'approbation"
    _inherit = ["tier.validation", "mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # --- tier.validation config ---
    _state_field = "state"
    _state_from = ["draft"]
    _state_to = ["approved"]
    _cancel_state = "cancelled"
    _tier_validation_manual_config = True

    # --- Champs ---
    name = fields.Char(
        string="Référence",
        readonly=True,
        copy=False,
        default="/",
    )
    categorie_id = fields.Many2one(
        "isic.approbation.categorie",
        string="Catégorie",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    demandeur_id = fields.Many2one(
        "res.users",
        string="Demandeur",
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        tracking=True,
        ondelete="restrict",
    )
    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("submitted", "Soumise"),
            ("approved", "Approuvée"),
            ("rejected", "Refusée"),
            ("cancelled", "Annulée"),
        ],
        string="État",
        default="draft",
        tracking=True,
        index=True,
    )

    # Dates
    date_demande = fields.Date(
        string="Date de la demande",
        default=fields.Date.today,
        required=True,
    )
    date_debut = fields.Date(string="Date de début")
    date_fin = fields.Date(string="Date de fin")

    # Contenu
    motif = fields.Text(string="Motif de la demande", required=True)
    observations = fields.Text(string="Observations")
    priorite = fields.Selection(
        [
            ("0", "Normale"),
            ("1", "Urgente"),
            ("2", "Très urgente"),
        ],
        string="Priorité",
        default="0",
    )
    piece_jointe = fields.Binary(string="Pièce jointe", attachment=True)
    nom_fichier = fields.Char(string="Nom du fichier")

    # Contexte académique
    annee_academique_id = fields.Many2one(
        "isic.annee.academique",
        string="Année académique",
        tracking=True,
        default=lambda self: self.env["isic.annee.academique"]._get_current(),
        ondelete="restrict",
    )

    # Résultat
    date_decision = fields.Datetime(string="Date de décision", readonly=True)
    motif_refus = fields.Text(string="Motif du refus", readonly=True)

    # --- Contraintes ---
    @api.constrains("date_debut", "date_fin")
    def _check_dates(self):
        for rec in self:
            if rec.date_debut and rec.date_fin and rec.date_fin < rec.date_debut:
                raise UserError(_("La date de fin doit être postérieure à la date de début."))

    # --- Workflow ---
    def action_submit(self):
        """Brouillon → Soumise : génère le numéro et lance la validation."""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Seule une demande en brouillon peut être soumise."))
            if rec.name == "/":
                seq = rec.categorie_id.sequence_id
                if seq:
                    rec.name = seq.next_by_id()
                else:
                    rec.name = self.env["ir.sequence"].next_by_code("isic.approbation.demande") or "/"
            rec.state = "submitted"
            if rec.categorie_id.approbation_requise:
                rec.with_context(skip_check_state_condition=True).request_validation()

    def action_approve(self):
        """Marque la demande comme approuvée."""
        self.write(
            {
                "state": "approved",
                "date_decision": fields.Datetime.now(),
            }
        )

    def action_reject(self, motif=False):
        """Marque la demande comme refusée."""
        self.write(
            {
                "state": "rejected",
                "date_decision": fields.Datetime.now(),
                "motif_refus": motif or "",
            }
        )

    def action_cancel(self):
        """Annulation par le demandeur."""
        for rec in self:
            if rec.state == "approved":
                raise UserError(_("Une demande approuvée ne peut pas être annulée."))
        self.write({"state": "cancelled"})
        self.mapped("review_ids").unlink()

    def action_reset_draft(self):
        """Remise en brouillon (direction uniquement)."""
        self.write(
            {
                "state": "draft",
                "date_decision": False,
                "motif_refus": False,
            }
        )
        self.mapped("review_ids").unlink()

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    # --- tier.validation overrides ---
    def _check_auto_transition(self):
        """Transition automatique quand toutes les reviews sont terminées."""
        for rec in self:
            if rec.state != "submitted":
                continue
            # Invalidate le cache pour relire validation_status depuis la DB
            rec.invalidate_recordset(["validation_status"])
            if rec.validation_status == "validated":
                rec.with_context(skip_tier_check=True).action_approve()
            elif rec.validation_status == "rejected":
                comments = rec.review_ids.filtered(lambda r: r.status == "rejected" and r.comment).mapped("comment")
                rec.with_context(skip_tier_check=True).action_reject(motif="; ".join(comments) if comments else False)

    def _validate_tier(self, tiers=False):
        """Override pour déclencher l'auto-transition après validation."""
        super()._validate_tier(tiers)
        self._check_auto_transition()

    def _rejected_tier(self, tiers=False):
        """Override pour déclencher l'auto-transition après rejet."""
        super()._rejected_tier(tiers)
        self._check_auto_transition()

    def _get_under_validation_exceptions(self):
        """Champs modifiables pendant la validation."""
        res = super()._get_under_validation_exceptions()
        res.extend(["observations", "piece_jointe", "nom_fichier", "priorite"])
        return res

    def _get_to_validate_message_name(self):
        return self.categorie_id.name or self._description
