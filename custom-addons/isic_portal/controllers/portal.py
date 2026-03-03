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
    # Portal home counters
    # ------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        Demande = request.env["isic.approbation.demande"]
        uid = request.env.uid

        if "demande_count" in counters:
            values["demande_count"] = Demande.search_count([("demandeur_id", "=", uid)])
        if "demande_pending_count" in counters:
            values["demande_pending_count"] = Demande.search_count(
                [("demandeur_id", "=", uid), ("state", "in", ("submitted", "draft"))]
            )
        if "demande_approved_count" in counters:
            values["demande_approved_count"] = Demande.search_count(
                [("demandeur_id", "=", uid), ("state", "=", "approved")]
            )
        if "document_count" in counters:
            # Count DMS files belonging to this user's partner (non-draft)
            DmsFile = request.env["dms.file"]
            partner_id = request.env.user.partner_id.id
            domain = [("partner_id", "=", partner_id), ("ged_state", "!=", "draft")]
            # sudo() justified: portal user has no DMS ACL, we filter by partner_id
            values["document_count"] = DmsFile.sudo().search_count(domain)

        return values

    # ------------------------------------------------------------------
    # Override home() to pass counters server-side for hero display
    # ------------------------------------------------------------------
    @http.route(["/my", "/my/home"], type="http", auth="user", website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()
        # Compute counters eagerly (hero renders them server-side, no async flash)
        counter_keys = ["demande_count", "demande_pending_count", "demande_approved_count", "document_count"]
        values.update(self._prepare_home_portal_values(counter_keys))
        return request.render("portal.portal_my_home", values)

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

    def _demande_get_searchbar_inputs(self):
        return {
            "reference": {"input": "reference", "label": _("Reference")},
            "categorie": {"input": "categorie", "label": _("Categorie")},
            "all": {"input": "all", "label": _("Tout")},
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
    def portal_my_demandes(self, page=1, sortby=None, filterby=None, search=None, search_in="all", **kw):
        Demande = request.env["isic.approbation.demande"]
        domain = [("demandeur_id", "=", request.env.uid)]

        searchbar_sortings = self._demande_get_searchbar_sortings()
        if not sortby or sortby not in searchbar_sortings:
            sortby = "date"

        searchbar_filters = self._demande_get_searchbar_filters()
        if not filterby or filterby not in searchbar_filters:
            filterby = "all"

        searchbar_inputs = self._demande_get_searchbar_inputs()

        # Apply filter
        domain += searchbar_filters[filterby]["domain"]

        # Apply search
        if search and search_in:
            if search_in == "reference":
                domain += [("name", "ilike", search)]
            elif search_in == "categorie":
                domain += [("categorie_id.name", "ilike", search)]
            else:  # "all"
                domain += ["|", ("name", "ilike", search), ("categorie_id.name", "ilike", search)]

        demande_count = Demande.search_count(domain)

        pager = portal_pager(
            url="/my/demandes",
            url_args={"sortby": sortby, "filterby": filterby, "search": search, "search_in": search_in},
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
            "searchbar_inputs": searchbar_inputs,
            "search_in": search_in,
            "search": search,
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

        # Build pipeline steps for progress display
        state_pipeline = [
            ("draft", _("Brouillon")),
            ("submitted", _("Soumise")),
            ("approved", _("Approuvee")),
        ]
        if demande_sudo.state == "rejected":
            state_pipeline = [
                ("draft", _("Brouillon")),
                ("submitted", _("Soumise")),
                ("rejected", _("Refusee")),
            ]

        values = {
            "demande": demande_sudo,
            "page_name": "demande_detail",
            "state_pipeline": state_pipeline,
        }
        # Setup chatter values (token, pid, hash for portal.message_thread)
        values = self._get_page_view_values(demande_sudo, access_token, values, "my_demandes_history", False, **kw)
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

    # ------------------------------------------------------------------
    # Profile: /my/profile
    # ------------------------------------------------------------------
    @http.route(
        "/my/profile",
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_profile(self, **kw):
        user = request.env.user
        partner = user.partner_id
        values = {
            "page_name": "profile",
            "partner": partner,
            "user": user,
        }
        return request.render("isic_portal.portal_my_profile", values)

    # ------------------------------------------------------------------
    # Documents: /my/documents
    # ------------------------------------------------------------------
    @http.route(
        ["/my/documents", "/my/documents/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_documents(self, page=1, doc_type=None, doc_state=None, search=None, **kw):
        DmsFile = request.env["dms.file"]
        DocType = request.env["isic.document.type"]

        # Base domain: only documents belonging to this user's partner (non-draft)
        partner_id = request.env.user.partner_id.id
        domain = [("partner_id", "=", partner_id), ("ged_state", "!=", "draft")]

        # Filter by document type
        if doc_type and doc_type.isdigit():
            domain += [("document_type_id", "=", int(doc_type))]

        # Filter by state
        if doc_state and doc_state in ("validated", "archived"):
            domain += [("ged_state", "=", doc_state)]

        # Search by name
        if search:
            domain += ["|", ("name", "ilike", search), ("reference", "ilike", search)]

        # sudo() justified: portal DMS access is controlled by dms.access model,
        # we only show non-draft and count via sudo
        doc_count = DmsFile.sudo().search_count(domain)

        pager = portal_pager(
            url="/my/documents",
            url_args={"doc_type": doc_type, "doc_state": doc_state, "search": search},
            total=doc_count,
            page=page,
            step=15,
        )

        documents = DmsFile.sudo().search(
            domain,
            order="write_date desc",
            limit=15,
            offset=pager["offset"],
        )

        # Available document types for filter dropdown
        # sudo() justified: portal user needs to see type names for filtering
        doc_types = DocType.sudo().search([("active", "=", True)], order="sequence, name")

        values = {
            "page_name": "documents",
            "documents": documents,
            "pager": pager,
            "doc_types": doc_types,
            "doc_type": doc_type,
            "doc_state": doc_state,
            "search": search,
        }
        return request.render("isic_portal.portal_my_documents", values)
