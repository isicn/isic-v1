from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    sidebar_type = fields.Selection(default="invisible")
    color_scheme = fields.Selection(
        [("light", "Light"), ("dark", "Dark")],
        string="Color Mode",
        default="light",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return [*super().SELF_READABLE_FIELDS, "color_scheme"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return [*super().SELF_WRITEABLE_FIELDS, "color_scheme"]
