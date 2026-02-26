from . import models


def _post_init_hook(env):
    """Set the portal dashboard as the default home action for internal users without one."""
    action = env.ref("isic_portal.isic_portal_dashboard_action", raise_if_not_found=False)
    if action:
        # Only set action_id on users that don't already have a custom home action
        internal_users = env["res.users"].search(
            [
                ("share", "=", False),
                ("id", "!=", env.ref("base.user_root").id),
                ("action_id", "=", False),
            ]
        )
        internal_users.sudo().write({"action_id": action.id})
