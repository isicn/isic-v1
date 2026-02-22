import base64
import logging
import os

from . import models  # noqa: F401

_logger = logging.getLogger(__name__)


def _post_init_hook(env):
    """Set ISIC branding on module installation."""
    # --- Company logo ---
    logo_path = os.path.join(
        os.path.dirname(__file__),
        "static",
        "src",
        "img",
        "isic_logo.png",
    )
    if os.path.isfile(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read())
        main_company = env.ref("base.main_company", raise_if_not_found=False)
        if main_company:
            vals = {
                "name": "ISIC",
                "logo": logo_data,
            }
            # Set sidebar logo for MuK AppsBar if field exists
            if "appbar_image" in main_company._fields:
                vals["appbar_image"] = logo_data
            main_company.write(vals)
            _logger.info("ISIC logo set on main company")
    else:
        _logger.warning("ISIC logo not found at %s", logo_path)

    # --- Hide MuK sidebar for all users ---
    if "sidebar_type" in env["res.users"]._fields:
        users = env["res.users"].search([("sidebar_type", "!=", "invisible")])
        if users:
            users.write({"sidebar_type": "invisible"})
            _logger.info("Sidebar set to 'invisible' for %d users", len(users))
