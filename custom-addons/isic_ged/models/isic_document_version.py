from odoo import api, fields, models
from odoo.tools import human_size


class IsicDocumentVersion(models.Model):
    _name = "isic.document.version"
    _description = "Version de document"
    _order = "version_number desc"
    _rec_name = "display_name"

    file_id = fields.Many2one(
        "dms.file",
        string="Fichier",
        required=True,
        ondelete="cascade",
        index=True,
    )
    version_number = fields.Integer(
        string="N° de version",
        required=True,
        readonly=True,
    )
    content = fields.Binary(
        string="Contenu",
        attachment=True,
        required=True,
    )
    checksum = fields.Char(
        string="Checksum SHA1",
        readonly=True,
        index=True,
    )
    size = fields.Float(
        string="Taille (octets)",
        readonly=True,
    )
    human_size = fields.Char(
        string="Taille",
        compute="_compute_human_size",
        store=True,
    )
    mimetype = fields.Char(
        string="Type MIME",
        readonly=True,
    )
    name = fields.Char(
        string="Nom du fichier",
        readonly=True,
    )
    author_id = fields.Many2one(
        "res.users",
        string="Auteur",
        readonly=True,
        default=lambda self: self.env.uid,
        ondelete="set null",
    )
    date = fields.Datetime(
        string="Date",
        readonly=True,
        default=fields.Datetime.now,
    )
    comment = fields.Text(string="Commentaire")
    display_name = fields.Char(
        compute="_compute_display_name",
    )

    _unique_version = models.Constraint(
        "UNIQUE(file_id, version_number)",
        "Le numéro de version doit être unique par fichier.",
    )

    @api.depends("size")
    def _compute_human_size(self):
        for rec in self:
            rec.human_size = human_size(rec.size) if rec.size else ""

    @api.depends("version_number", "date")
    def _compute_display_name(self):
        for rec in self:
            date_str = rec.date.strftime("%d/%m/%Y %H:%M") if rec.date else ""
            rec.display_name = f"v{rec.version_number} — {date_str}"

    def action_restore(self):
        """Restore this version's content to the parent file."""
        self.ensure_one()
        self.file_id.with_context(restore_version_id=self.id).action_restore_version()
