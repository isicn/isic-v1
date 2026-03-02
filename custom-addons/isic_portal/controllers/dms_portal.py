from odoo.addons.dms.controllers.portal import CustomerPortal as DmsPortal
from odoo.http import request


class IsicDmsPortal(DmsPortal):
    """Override DMS portal to hide draft documents for portal users."""

    def _get_files(self, access_token, dms_directory_id, search, search_in, sort_br):
        files = super()._get_files(access_token, dms_directory_id, search, search_in, sort_br)
        if request.env.user.has_group("base.group_portal"):
            files = files.filtered(lambda f: f.ged_state != "draft")
        return files
