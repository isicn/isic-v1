import fnmatch

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class IsicDocumentClassificationRule(models.Model):
    _name = "isic.document.classification.rule"
    _description = "Règle de classification documentaire"
    _order = "sequence, id"

    name = fields.Char(string="Nom", required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    match_type = fields.Selection(
        [
            ("filename", "Nom de fichier"),
            ("extension", "Extension"),
            ("directory", "Répertoire"),
            ("mimetype", "Type MIME"),
        ],
        string="Critère",
        required=True,
    )
    match_pattern = fields.Char(
        string="Pattern",
        required=True,
        help="Pattern de correspondance. Pour les noms de fichier, utilisez * comme joker (ex: PV_*, NDS_*).",
    )
    match_case_sensitive = fields.Boolean(
        string="Sensible à la casse",
        default=False,
    )
    document_type_id = fields.Many2one(
        "isic.document.type",
        string="Type de document",
        ondelete="cascade",
        help="Type de document à affecter automatiquement.",
    )
    tag_ids = fields.Many2many(
        "dms.tag",
        string="Tags",
        help="Tags à ajouter automatiquement.",
    )

    @api.constrains("match_pattern")
    def _check_pattern(self):
        for rec in self:
            if not rec.match_pattern or not rec.match_pattern.strip():
                raise ValidationError(_("Le pattern de correspondance ne peut pas être vide."))

    def _match(self, dms_file):
        """Test if this rule matches the given dms.file record.

        :param dms_file: dms.file recordset (single)
        :return: True if the rule matches
        """
        self.ensure_one()
        pattern = self.match_pattern.strip()

        if self.match_type == "filename":
            value = dms_file.name or ""
            if not self.match_case_sensitive:
                value = value.lower()
                pattern = pattern.lower()
            return fnmatch.fnmatch(value, pattern)

        if self.match_type == "extension":
            ext = dms_file.extension or ""
            if not self.match_case_sensitive:
                ext = ext.lower()
                pattern = pattern.lower()
            # Allow pattern with or without leading dot
            pattern = pattern.lstrip(".")
            ext = ext.lstrip(".")
            return ext == pattern

        if self.match_type == "directory":
            dir_name = dms_file.directory_id.complete_name or ""
            if not self.match_case_sensitive:
                dir_name = dir_name.lower()
                pattern = pattern.lower()
            return fnmatch.fnmatch(dir_name, f"*{pattern}*")

        if self.match_type == "mimetype":
            mime = dms_file.mimetype or ""
            if not self.match_case_sensitive:
                mime = mime.lower()
                pattern = pattern.lower()
            return mime == pattern

        return False
