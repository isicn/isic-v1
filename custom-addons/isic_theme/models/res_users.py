from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    sidebar_type = fields.Selection(default="invisible")
