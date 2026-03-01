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

    auto_sequence = fields.Boolean(
        string="Séquence automatique",
        default=True,
        help="Génère automatiquement une référence pour chaque demande de cette catégorie.",
    )
    prefix_code = fields.Char(
        string="Code préfixe",
        help="Préfixe utilisé pour la numérotation. Ex: DEM/ATT → DEM/ATT/2026/0001",
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
    is_user_allowed = fields.Boolean(
        compute="_compute_is_user_allowed",
        search="_search_is_user_allowed",
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

    @api.depends_context("uid")
    @api.depends("groupe_demandeur_ids")
    def _compute_is_user_allowed(self):
        user_groups = self.env.user.group_ids
        for rec in self:
            if not rec.groupe_demandeur_ids:
                rec.is_user_allowed = True
            else:
                rec.is_user_allowed = bool(rec.groupe_demandeur_ids & user_groups)

    def _search_is_user_allowed(self, operator, value):
        # Normalize: is_user_allowed = True OR is_user_allowed != False
        positive = (operator == "=" and value) or (operator == "!=" and not value)
        user_group_ids = self.env.user.group_ids.ids
        if not user_group_ids:
            if positive:
                return [("groupe_demandeur_ids", "=", False)]
            else:
                return [("groupe_demandeur_ids", "!=", False)]
        # Categories with no restriction OR user is in an allowed group
        all_cats = self.search([])
        allowed_ids = []
        for cat in all_cats:
            if not cat.groupe_demandeur_ids or (cat.groupe_demandeur_ids & self.env.user.group_ids):
                allowed_ids.append(cat.id)
        if positive:
            return [("id", "in", allowed_ids)]
        else:
            return [("id", "not in", allowed_ids)]

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

    @api.onchange("code")
    def _onchange_code(self):
        if self.code and not self.prefix_code:
            self.prefix_code = f"DEM/{self.code}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("auto_sequence", True) and not vals.get("prefix_code") and vals.get("code"):
                vals["prefix_code"] = f"DEM/{vals['code']}"
        records = super().create(vals_list)
        for rec in records:
            if rec.auto_sequence and not rec.sequence_id:
                rec._create_sequence()
        records.filtered("approbateur_ids")._sync_tier_definitions()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "approbateur_ids" in vals:
            self._sync_tier_definitions()
        for rec in self:
            if rec.auto_sequence and not rec.sequence_id:
                rec._create_sequence()
            elif rec.auto_sequence and rec.sequence_id and "prefix_code" in vals:
                rec.sequence_id.sudo().write({"prefix": f"{rec.prefix_code}/%(year)s/"})
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
            # Attrape les deux formats de domaine: par ID et par code
            existing_tier_ids = approbateurs.mapped("tier_definition_id").ids
            orphans = TierDef.search(
                [
                    ("model_id", "=", model_id),
                    "|",
                    ("definition_domain", "like", f"'categorie_id', '=', {cat.id})]"),
                    ("definition_domain", "like", f"'categorie_id.code', '=', '{cat.code}')]"),
                    ("id", "not in", existing_tier_ids),
                ]
            )
            orphans.unlink()

    def _create_sequence(self):
        """Crée une séquence ir.sequence pour la numérotation automatique des demandes."""
        self.ensure_one()
        prefix = self.prefix_code or f"DEM/{self.code}"
        seq = (
            self.env["ir.sequence"]
            .sudo()
            .create(
                {
                    "name": f"Demande {self.name}",
                    "code": f"isic.approbation.demande.{self.code.lower()}",
                    "prefix": f"{prefix}/%(year)s/",
                    "padding": 4,
                    "company_id": False,
                }
            )
        )
        self.sequence_id = seq
