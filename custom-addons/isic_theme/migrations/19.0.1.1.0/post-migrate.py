import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Hide MuK sidebar for all existing users."""
    cr.execute(
        "UPDATE res_users SET sidebar_type = 'invisible' WHERE sidebar_type != 'invisible' OR sidebar_type IS NULL"
    )
    _logger.info("Migration 19.0.1.1.0: sidebar set to 'invisible' for all users")
