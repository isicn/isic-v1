import logging

from . import controllers, models, tests

_logger = logging.getLogger(__name__)


def _post_init_hook(env):
    """Post-install: hide DMS menus + create full-text search index."""
    # Hide DMS menus — users should use ISIC GED menus instead
    dms_root = env.ref("dms.main_menu_dms", raise_if_not_found=False)
    if dms_root:
        children = env["ir.ui.menu"].search([("id", "child_of", dms_root.id)])
        children.write({"active": False})
        _logger.info("DMS menus hidden (%d menus deactivated)", len(children))

    # Create tsvector column and GIN index for full-text search.
    # This column is managed outside the ORM (no native tsvector field in Odoo).
    # Updates are done via raw SQL in dms_file._update_fulltext_index().
    env.cr.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'dms_file' AND column_name = 'fulltext_tsvector'
            ) THEN
                ALTER TABLE dms_file ADD COLUMN fulltext_tsvector tsvector;
            END IF;
        END $$;
        """
    )
    env.cr.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dms_file_fulltext
        ON dms_file USING gin(fulltext_tsvector);
        """
    )
    _logger.info("Full-text search index created on dms_file")
