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

    # Circuit preview (computed from category)
    approbateur_preview_ids = fields.Many2many(
        "isic.approbation.approbateur",
        string="Circuit de validation prévu",
        compute="_compute_approbateur_preview_ids",
    )

    # --- Contraintes ---
    @api.constrains("date_debut", "date_fin")
    def _check_dates(self):
        for rec in self:
            if rec.date_debut and rec.date_fin and rec.date_fin < rec.date_debut:
                raise UserError(_("La date de fin doit être postérieure à la date de début."))

    @api.depends("categorie_id.approbateur_ids")
    def _compute_approbateur_preview_ids(self):
        for rec in self:
            rec.approbateur_preview_ids = rec.categorie_id.approbateur_ids

    # --- Workflow ---
    def action_submit(self):
        """Brouillon → Soumise : génère le numéro et lance la validation."""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Seule une demande en brouillon peut être soumise."))
            allowed_groups = rec.categorie_id.groupe_demandeur_ids
            if allowed_groups and not (allowed_groups & rec.demandeur_id.group_ids):
                raise UserError(
                    _("Vous n'êtes pas autorisé à soumettre une demande de type « %s ».", rec.categorie_id.name)
                )
            if rec.name == "/":
                seq = rec.categorie_id.sequence_id
                if seq:
                    rec.name = seq.next_by_id()
                else:
                    rec.name = self.env["ir.sequence"].next_by_code("isic.approbation.demande") or "/"
            rec.state = "submitted"
            if rec.categorie_id.approbation_requise:
                rec.with_context(skip_check_state_condition=True).request_validation()
            rec._sync_review_activities()

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
        self._sync_review_activities()

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
        self._sync_review_activities()

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    # --- Activités ---
    def _sync_review_activities(self):
        """Synchronise les activités avec l'état des reviews.

        Supprime les activités d'approbation obsolètes et planifie
        de nouvelles activités pour les approbateurs en attente.
        """
        activity_type = self.env.ref(
            "isic_approbation.mail_activity_type_approbation",
            raise_if_not_found=False,
        )
        if not activity_type:
            return
        for rec in self:
            rec.activity_ids.filtered(lambda a, at=activity_type: a.activity_type_id == at).unlink()
            if rec.state != "submitted":
                continue
            # S'assurer que les reviews waiting sont avancées en pending
            rec.review_ids._advance_pending_status()
            pending_reviews = rec.review_ids.filtered(lambda r: r.status == "pending")
            for review in pending_reviews:
                for user in review.reviewer_ids:
                    rec.activity_schedule(
                        act_type_xmlid="isic_approbation.mail_activity_type_approbation",
                        summary=_("Approbation requise : %s", rec.name or rec.categorie_id.name),
                        note=_(
                            "La demande %(ref)s de %(user)s nécessite votre approbation.",
                            ref=rec.name,
                            user=rec.demandeur_id.name,
                        ),
                        user_id=user.id,
                    )

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
        """Override pour déclencher l'auto-transition et les activités après validation."""
        super()._validate_tier(tiers)
        self._check_auto_transition()
        self._sync_review_activities()

    def _rejected_tier(self, tiers=False):
        """Override pour déclencher l'auto-transition et les activités après rejet."""
        super()._rejected_tier(tiers)
        self._check_auto_transition()
        self._sync_review_activities()

    def _get_under_validation_exceptions(self):
        """Champs modifiables pendant la validation."""
        res = super()._get_under_validation_exceptions()
        res.extend(["observations", "piece_jointe", "nom_fichier", "priorite"])
        return res

    def _get_to_validate_message_name(self):
        return self.categorie_id.name or self._description
