import logging

from . import models

_logger = logging.getLogger(__name__)


def _post_init_hook(env):
    """Hide DMS from the Apps menu — users should use ISIC GED instead."""
    module = env["ir.module.module"].search([("name", "=", "dms"), ("state", "=", "installed")])
    if module:
        module.write({"application": False})
        _logger.info("DMS module hidden from Apps menu")
