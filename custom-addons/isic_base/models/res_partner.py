from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # ── Profil personnel ──────────────────────────────────────────────
    cin = fields.Char(string="CIN", size=20, help="Carte d'Identité Nationale")
    date_naissance = fields.Date(string="Date de naissance")
    lieu_naissance = fields.Char(string="Lieu de naissance")
    genre = fields.Selection(
        [("M", "Masculin"), ("F", "Féminin")],
        string="Genre",
    )
    situation_familiale = fields.Selection(
        [
            ("celibataire", "Célibataire"),
            ("marie", "Marié(e)"),
            ("divorce", "Divorcé(e)"),
            ("veuf", "Veuf(ve)"),
        ],
        string="Situation familiale",
    )
    nationalite_id = fields.Many2one("res.country", string="Nationalité")
    adresse_personnelle = fields.Text(string="Adresse personnelle")
    telephone_personnel = fields.Char(string="Téléphone personnel")
    contact_urgence_nom = fields.Char(string="Contact d'urgence")
    contact_urgence_tel = fields.Char(string="Tél. contact d'urgence")

    # ── Champs synchronisés depuis LDAP (lecture seule pour les users CAS) ──
    ldap_synced = fields.Boolean(
        string="Synchronisé LDAP",
        default=False,
        help="Indique que ce contact est synchronisé depuis le référentiel LDAP. "
        "Les champs nom, email et fonction sont mis à jour automatiquement à chaque connexion CAS.",
    )

    # ── Enseignant ────────────────────────────────────────────────────
    is_enseignant = fields.Boolean(string="Enseignant", default=False)
    grade = fields.Selection(
        [
            ("pes", "PES — Professeur de l'Enseignement Supérieur"),
            ("ph", "PH — Professeur Habilité"),
            ("pa", "PA — Professeur Assistant"),
            ("vacataire", "Vacataire"),
        ],
        string="Grade",
    )
    specialite = fields.Char(string="Spécialité")
    date_recrutement = fields.Date(string="Date de recrutement")
    volume_horaire_statutaire = fields.Float(string="Volume horaire statutaire", help="Volume horaire annuel en heures")

    # ── Fiscal marocain (entreprise / client / fournisseur) ──────────
    ice = fields.Char(string="ICE", size=15, help="Identifiant Commun de l'Entreprise (15 chiffres)")
    identifiant_fiscal = fields.Char(string="Identifiant Fiscal (IF)")
    rc = fields.Char(string="Registre de Commerce (RC)")
    ville_rc = fields.Char(string="Ville du RC")
    cnss = fields.Char(string="N° CNSS")
    patente = fields.Char(string="N° Patente")
    tp = fields.Char(string="Taxe Professionnelle (TP)")

    @api.constrains("ice")
    def _check_ice(self):
        for partner in self:
            if partner.ice and (len(partner.ice) != 15 or not partner.ice.isdigit()):
                raise ValidationError(_("L'ICE doit contenir exactement 15 chiffres."))

    @api.constrains("cin")
    def _check_cin(self):
        for partner in self:
            if partner.cin and len(partner.cin) < 3:
                raise ValidationError(_("Le numéro CIN semble invalide (minimum 3 caractères)."))
