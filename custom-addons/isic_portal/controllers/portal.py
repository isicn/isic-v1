import base64
import logging

from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

_logger = logging.getLogger(__name__)

# Categories ouvertes aux etudiants (codes)
PORTAL_CATEGORY_CODES = ("ATT", "MATERIEL", "DIVERS")


class IsicPortal(CustomerPortal):
    # ------------------------------------------------------------------
    # Portal home counter
    # ------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "demande_count" in counters:
            Demande = request.env["isic.approbation.demande"]
            values["demande_count"] = Demande.search_count([("demandeur_id", "=", request.env.uid)])
        return values

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _demande_get_searchbar_sortings(self):
        return {
            "date": {"label": _("Date"), "order": "create_date desc"},
            "name": {"label": _("Reference"), "order": "name desc"},
            "state": {"label": _("Etat"), "order": "state asc"},
        }

    def _demande_get_searchbar_filters(self):
        return {
            "all": {"label": _("Toutes"), "domain": []},
            "submitted": {"label": _("Soumises"), "domain": [("state", "=", "submitted")]},
            "approved": {"label": _("Approuvees"), "domain": [("state", "=", "approved")]},
            "rejected": {"label": _("Refusees"), "domain": [("state", "=", "rejected")]},
        }

    def _portal_categories(self):
        """Return categories available to portal students."""
        return (
            request.env["isic.approbation.categorie"]
            .sudo()
            .search([("code", "in", list(PORTAL_CATEGORY_CODES)), ("active", "=", True)])
        )

    # ------------------------------------------------------------------
    # List: /my/demandes
    # ------------------------------------------------------------------
    @http.route(
        ["/my/demandes", "/my/demandes/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_demandes(self, page=1, sortby=None, filterby=None, **kw):
        Demande = request.env["isic.approbation.demande"]
        domain = [("demandeur_id", "=", request.env.uid)]

        searchbar_sortings = self._demande_get_searchbar_sortings()
        if not sortby or sortby not in searchbar_sortings:
            sortby = "date"

        searchbar_filters = self._demande_get_searchbar_filters()
        if not filterby or filterby not in searchbar_filters:
            filterby = "all"

        domain += searchbar_filters[filterby]["domain"]
        demande_count = Demande.search_count(domain)

        pager = portal_pager(
            url="/my/demandes",
            url_args={"sortby": sortby, "filterby": filterby},
            total=demande_count,
            page=page,
            step=10,
        )
        demandes = Demande.search(
            domain,
            order=searchbar_sortings[sortby]["order"],
            limit=10,
            offset=pager["offset"],
        )
        values = {
            "demandes": demandes,
            "page_name": "demandes",
            "pager": pager,
            "default_url": "/my/demandes",
            "searchbar_sortings": searchbar_sortings,
            "sortby": sortby,
            "searchbar_filters": searchbar_filters,
            "filterby": filterby,
        }
        return request.render("isic_portal.portal_my_demandes", values)

    # ------------------------------------------------------------------
    # Detail: /my/demandes/<id>
    # ------------------------------------------------------------------
    @http.route(
        "/my/demandes/<int:demande_id>",
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_demande_detail(self, demande_id, access_token=None, **kw):
        try:
            demande_sudo = self._document_check_access("isic.approbation.demande", demande_id, access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")

        values = {
            "demande": demande_sudo,
            "page_name": "demande_detail",
        }
        return request.render("isic_portal.portal_my_demande_detail", values)

    # ------------------------------------------------------------------
    # New: /my/demandes/new
    # ------------------------------------------------------------------
    @http.route(
        "/my/demandes/new",
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_demande_new(self, **kw):
        categories = self._portal_categories()
        values = {
            "categories": categories,
            "page_name": "demande_new",
            "error": {},
            "error_message": [],
        }
        return request.render("isic_portal.portal_my_demande_new", values)

    # ------------------------------------------------------------------
    # Submit: POST /my/demandes/submit
    # ------------------------------------------------------------------
    @http.route(
        "/my/demandes/submit",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_my_demande_submit(self, **post):
        error = {}
        error_message = []

        # --- Validate required fields ---
        categorie_id = post.get("categorie_id")
        motif = post.get("motif", "").strip()

        if not categorie_id:
            error["categorie_id"] = "missing"
            error_message.append(_("Veuillez selectionner une categorie."))
        if not motif:
            error["motif"] = "missing"
            error_message.append(_("Le motif est obligatoire."))

        # --- Validate category is in allowed portal codes ---
        categorie = None
        if categorie_id:
            categorie = (
                request.env["isic.approbation.categorie"]
                .sudo()
                .browse(int(categorie_id))
                .filtered(lambda c: c.code in PORTAL_CATEGORY_CODES and c.active)
            )
            if not categorie:
                error["categorie_id"] = "invalid"
                error_message.append(_("Categorie non autorisee."))

        if error:
            categories = self._portal_categories()
            values = {
                "categories": categories,
                "page_name": "demande_new",
                "error": error,
                "error_message": error_message,
                **post,
            }
            return request.render("isic_portal.portal_my_demande_new", values)

        # --- Build vals ---
        vals = {
            "categorie_id": categorie.id,
            "demandeur_id": request.env.uid,
            "motif": motif,
            "priorite": post.get("priorite", "0"),
            "observations": post.get("observations", "").strip() or False,
        }
        if post.get("date_debut"):
            vals["date_debut"] = post["date_debut"]
        if post.get("date_fin"):
            vals["date_fin"] = post["date_fin"]

        # --- Handle file upload ---
        fichier = post.get("piece_jointe")
        if fichier:
            vals["piece_jointe"] = base64.b64encode(fichier.read())
            vals["nom_fichier"] = fichier.filename

        # --- Create with sudo (portal user has no create ACL) + auto-submit ---
        # sudo() justified: portal user creates via controlled form, demandeur_id forced to current user
        demande = request.env["isic.approbation.demande"].sudo().create(vals)
        demande.action_submit()

        return request.redirect(f"/my/demandes/{demande.id}")
