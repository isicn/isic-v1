import logging

from . import models

_logger = logging.getLogger(__name__)


def _post_init_hook(env):
    """Hide DMS menus — users should use ISIC GED menus instead."""
    dms_root = env.ref("dms.main_menu_dms", raise_if_not_found=False)
    if dms_root:
        # Deactivate DMS root menu and all its children
        children = env["ir.ui.menu"].search([("id", "child_of", dms_root.id)])
        children.write({"active": False})
        _logger.info("DMS menus hidden (%d menus deactivated)", len(children))
