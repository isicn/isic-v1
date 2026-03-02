from . import controllers


def _post_init_cleanup(env):
    """Fix ISIC menu parent and remove default Odoo website menus.

    website.main_menu is a shared template (no website_id). Each website gets
    its own root menu copy. We need to re-parent ISIC menus under the actual
    per-website root menu and delete any leftover default menus.
    """
    website = env.ref("website.default_website", raise_if_not_found=False)
    if not website:
        return

    # Find the per-website root menu (the actual root, not the shared template)
    website_root = env["website.menu"].search(
        [("website_id", "=", website.id), ("parent_id", "=", False)],
        limit=1,
    )
    if not website_root:
        return

    # ISIC menu xmlids
    isic_xmlids = [
        "isic_website.menu_home",
        "isic_website.menu_institut",
        "isic_website.menu_formations",
        "isic_website.menu_vie_etudiante",
        "isic_website.menu_recherche",
        "isic_website.menu_actualites",
        "isic_website.menu_contact",
    ]
    isic_menus = env["website.menu"]
    for xmlid in isic_xmlids:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            isic_menus |= rec

    # Re-parent ISIC menus under the correct per-website root
    if isic_menus:
        isic_menus.write({"parent_id": website_root.id})

    # Delete all non-ISIC child menus of the website root
    default_menus = env["website.menu"].search([
        ("parent_id", "=", website_root.id),
        ("website_id", "=", website.id),
        ("id", "not in", isic_menus.ids),
    ])
    if default_menus:
        default_menus.unlink()
