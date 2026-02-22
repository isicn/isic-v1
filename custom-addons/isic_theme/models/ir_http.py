from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def color_scheme(self):
        if request and request.env.user and request.env.user.color_scheme == "dark":
            return "dark"
        return "light"
