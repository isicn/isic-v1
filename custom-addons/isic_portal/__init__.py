from . import controllers, models


def _post_init_hook(env):
    """Add group_isic_etudiant to portal categories (ATT, MATERIEL, DIVERS)."""
    etudiant_group = env.ref("isic_base.group_isic_etudiant", raise_if_not_found=False)
    if not etudiant_group:
        return
    categories = (
        env["isic.approbation.categorie"]
        .sudo()
        .search(
            [
                ("code", "in", ["ATT", "MATERIEL", "DIVERS"]),
                ("active", "=", True),
            ]
        )
    )
    categories.write({"groupe_demandeur_ids": [(4, etudiant_group.id)]})
