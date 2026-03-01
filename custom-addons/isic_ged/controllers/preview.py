import base64
import re

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


def _sanitize_filename(name):
    """Remove characters that could be used for header injection."""
    if not name:
        return "document"
    return re.sub(r'["\\\r\n]', "_", name)


class IsicGedPreview(http.Controller):
    @http.route("/isic_ged/preview/<int:file_id>", type="http", auth="user")
    def preview_file(self, file_id, **kwargs):
        """Serve a file with its original Content-Type for in-browser preview.

        Works for PDF (browser native viewer) and images.
        """
        dms_file = request.env["dms.file"].browse(file_id)
        if not dms_file.exists():
            return request.not_found()

        try:
            dms_file.check_access("read")
            dms_file.check_access_rule("read")
        except AccessError:
            return request.not_found()

        content = dms_file.content
        if not content:
            return request.not_found()

        binary = base64.b64decode(content)
        mimetype = dms_file.mimetype or "application/octet-stream"
        filename = _sanitize_filename(dms_file.name)

        return request.make_response(
            binary,
            headers=[
                ("Content-Type", mimetype),
                ("Content-Length", str(len(binary))),
                ("Content-Disposition", f'inline; filename="{filename}"'),
            ],
        )
