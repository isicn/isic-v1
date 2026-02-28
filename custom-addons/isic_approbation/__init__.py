import ast
import logging

from . import models

_logger = logging.getLogger(__name__)


def _post_init_hook(env):
    """Migre les tier.definition existants en isic.approbation.approbateur."""
    TierDef = env["tier.definition"]
    Approbateur = env["isic.approbation.approbateur"]
    Categorie = env["isic.approbation.categorie"]

    model_id = env["ir.model"]._get_id("isic.approbation.demande")
    tiers = TierDef.search(
        [("model_id", "=", model_id)],
        order="sequence desc",
    )

    # Regrouper par catégorie
    cat_tiers = {}
    for tier in tiers:
        cat_id = _extract_categorie_id(tier.definition_domain, Categorie)
        if cat_id:
            cat_tiers.setdefault(cat_id, []).append(tier)

    for cat_id, tier_list in cat_tiers.items():
        # Vérifier qu'il n'y a pas déjà des approbateurs pour cette catégorie
        existing = Approbateur.search_count([("categorie_id", "=", cat_id)])
        if existing:
            continue

        for idx, tier in enumerate(tier_list):
            seq = (idx + 1) * 10
            vals = {
                "categorie_id": cat_id,
                "sequence": seq,
                "review_type": tier.review_type if tier.review_type in ("group", "individual") else "group",
                "has_comment": tier.has_comment,
                "tier_definition_id": tier.id,
            }
            if tier.review_type == "group" and tier.reviewer_group_id:
                vals["reviewer_group_id"] = tier.reviewer_group_id.id
            elif tier.review_type == "individual" and tier.reviewer_id:
                vals["reviewer_id"] = tier.reviewer_id.id
            else:
                vals["reviewer_group_id"] = tier.reviewer_group_id.id if tier.reviewer_group_id else False

            Approbateur.create(vals)

    _logger.info("post_init_hook: migré %d tier.definition vers approbateur_ids", len(tiers))


def _extract_categorie_id(domain_str, Categorie):
    """Extrait le categorie_id depuis un domain tier.definition."""
    if not domain_str:
        return False
    try:
        domain = ast.literal_eval(domain_str)
    except (ValueError, SyntaxError):
        return False

    for leaf in domain:
        if not isinstance(leaf, (list, tuple)) or len(leaf) != 3:
            continue
        field, op, value = leaf
        if op != "=":
            continue
        if field == "categorie_id":
            return value
        if field == "categorie_id.code":
            cat = Categorie.search([("code", "=", value)], limit=1)
            return cat.id if cat else False
    return False
