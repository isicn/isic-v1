from odoo import api, fields, models


class IsicApprobationCategorie(models.Model):
    _name = "isic.approbation.categorie"
    _description = "Catégorie de demande d'approbation"
    _order = "sequence, name"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Nom", required=True, translate=True, tracking=True)
    code = fields.Char(string="Code", required=True, tracking=True)
    description = fields.Text(string="Description", translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    icon = fields.Char(string="Icône", help="Classe Font Awesome, ex: fa-plane")
    color = fields.Integer(string="Couleur", default=0)

    approbation_requise = fields.Boolean(
        string="Approbation requise",
        default=True,
        help="Si coché, les demandes de cette catégorie nécessitent une validation.",
    )
    nombre_niveaux = fields.Integer(
        string="Nombre de niveaux",
        default=1,
        help="Nombre indicatif de niveaux d'approbation (la configuration réelle est dans les définitions de tiers).",
    )
    delai_traitement = fields.Integer(
        string="Délai de traitement (jours)",
        default=5,
        help="Délai indicatif en jours pour le traitement d'une demande.",
    )

    sequence_id = fields.Many2one(
        "ir.sequence",
        string="Séquence",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )
    groupe_demandeur_ids = fields.Many2many(
        "res.groups",
        string="Groupes autorisés",
        help="Groupes autorisés à créer ce type de demande. Vide = tous les utilisateurs internes.",
    )

    approbateur_ids = fields.One2many(
        "isic.approbation.approbateur",
        "categorie_id",
        string="Approbateurs",
        copy=True,
    )

    demande_ids = fields.One2many(
        "isic.approbation.demande",
        "categorie_id",
        string="Demandes",
    )
    demande_count = fields.Integer(
        string="Nombre de demandes",
        compute="_compute_demande_count",
    )

    _unique_code = models.Constraint(
        "UNIQUE(code)",
        "Le code de la catégorie doit être unique.",
    )

    @api.depends("demande_ids")
    def _compute_demande_count(self):
        data = self.env["isic.approbation.demande"]._read_group(
            [("categorie_id", "in", self.ids)],
            groupby=["categorie_id"],
            aggregates=["__count"],
        )
        counts = {cat.id: count for cat, count in data}
        for rec in self:
            rec.demande_count = counts.get(rec.id, 0)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.sequence_id:
                rec._create_sequence()
        records.filtered("approbateur_ids")._sync_tier_definitions()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "approbateur_ids" in vals:
            self._sync_tier_definitions()
        return res

    def _sync_tier_definitions(self):
        """Synchronise les approbateur_ids vers les tier.definition du moteur OCA."""
        TierDef = self.env["tier.definition"].sudo()
        model_id = self.env["ir.model"]._get_id("isic.approbation.demande")

        for cat in self:
            approbateurs = cat.approbateur_ids.sorted("sequence")
            count = len(approbateurs)

            for idx, appro in enumerate(approbateurs):
                is_first = idx == 0
                # OCA convention: order="sequence desc" → higher sequence = approves first
                tier_seq = 1000 - (idx * 10)

                vals = {
                    "name": f"{cat.name} — {appro.name}",
                    "model_id": model_id,
                    "review_type": appro.review_type,
                    "definition_domain": f"[('categorie_id', '=', {cat.id})]",
                    "sequence": tier_seq,
                    "approve_sequence": count > 1,
                    "has_comment": appro.has_comment,
                    "notify_on_create": is_first,
                    "notify_on_pending": not is_first,
                }
                if appro.review_type == "group":
                    vals["reviewer_group_id"] = appro.reviewer_group_id.id
                    vals["reviewer_id"] = False
                else:
                    vals["reviewer_id"] = appro.reviewer_id.id
                    vals["reviewer_group_id"] = False

                if appro.tier_definition_id:
                    appro.tier_definition_id.write(vals)
                else:
                    tier = TierDef.create(vals)
                    appro.tier_definition_id = tier

            # Supprimer les tier.definition orphelins liés à cette catégorie
            existing_tier_ids = approbateurs.mapped("tier_definition_id").ids
            # Suffixe ")]" empêche les faux positifs (cat.id=1 ne matche pas id=10)
            orphans = TierDef.search(
                [
                    ("model_id", "=", model_id),
                    ("definition_domain", "like", f"'categorie_id', '=', {cat.id})]"),
                    ("id", "not in", existing_tier_ids),
                ]
            )
            orphans.unlink()

    def _create_sequence(self):
        """Crée une séquence ir.sequence pour la numérotation automatique des demandes."""
        self.ensure_one()
        seq = (
            self.env["ir.sequence"]
            .sudo()
            .create(
                {
                    "name": f"Demande {self.name}",
                    "code": f"isic.approbation.demande.{self.code.lower()}",
                    "prefix": f"DEM/{self.code}/%(year)s/",
                    "padding": 4,
                    "company_id": False,
                }
            )
        )
        self.sequence_id = seq
