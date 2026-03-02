import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class IsicWebsite(http.Controller):
    # ------------------------------------------------------------------
    # Page: Accueil (/)
    # ------------------------------------------------------------------
    @http.route("/", type="http", auth="public", website=True, sitemap=True)
    def homepage(self, **kw):
        # Fetch latest 3 blog posts for the "Actualites" section
        BlogPost = request.env["blog.post"]
        latest_posts = BlogPost.sudo().search(
            [("website_published", "=", True)],
            order="published_date desc, id desc",
            limit=3,
        )
        values = {
            "latest_posts": latest_posts,
        }
        return request.render("isic_website.page_home", values)

    # ------------------------------------------------------------------
    # Page: L'Institut (/institut)
    # ------------------------------------------------------------------
    @http.route("/institut", type="http", auth="public", website=True, sitemap=True)
    def institut(self, **kw):
        return request.render("isic_website.page_institut")

    # ------------------------------------------------------------------
    # Page: Formations (/formations)
    # ------------------------------------------------------------------
    @http.route("/formations", type="http", auth="public", website=True, sitemap=True)
    def formations(self, **kw):
        return request.render("isic_website.page_formations")

    # ------------------------------------------------------------------
    # Page: Vie Etudiante (/vie-etudiante)
    # ------------------------------------------------------------------
    @http.route("/vie-etudiante", type="http", auth="public", website=True, sitemap=True)
    def vie_etudiante(self, **kw):
        return request.render("isic_website.page_vie_etudiante")

    # ------------------------------------------------------------------
    # Page: Recherche et Cooperation (/recherche)
    # ------------------------------------------------------------------
    @http.route("/recherche", type="http", auth="public", website=True, sitemap=True)
    def recherche(self, **kw):
        return request.render("isic_website.page_recherche")

    # ------------------------------------------------------------------
    # Page: Contact (/contact)
    # ------------------------------------------------------------------
    @http.route("/contact", type="http", auth="public", website=True, sitemap=True)
    def contact(self, **kw):
        return request.render("isic_website.page_contact", {"success": False, "error": {}})

    @http.route("/contact/submit", type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def contact_submit(self, **post):
        error = {}
        name = post.get("name", "").strip()
        email = post.get("email", "").strip()
        subject = post.get("subject", "").strip()
        message = post.get("message", "").strip()

        if not name:
            error["name"] = _("Le nom est obligatoire.")
        if not email:
            error["email"] = _("L'email est obligatoire.")
        if not message:
            error["message"] = _("Le message est obligatoire.")

        if error:
            return request.render(
                "isic_website.page_contact",
                {
                    "success": False,
                    "error": error,
                    "name": name,
                    "email": email,
                    "subject": subject,
                    "message": message,
                },
            )

        # Send email via mail.mail
        company = request.env.company
        mail_values = {
            "subject": f"[ISIC Contact] {subject or 'Sans objet'}",
            "body_html": f"""
                <p><strong>Nom :</strong> {name}</p>
                <p><strong>Email :</strong> {email}</p>
                <p><strong>Objet :</strong> {subject or "N/A"}</p>
                <hr/>
                <p>{message}</p>
            """,
            "email_from": email,
            "email_to": company.email or "contact@isic.ac.ma",
            "auto_delete": True,
        }
        # sudo() justified: public user sends contact form, no ACL on mail.mail
        request.env["mail.mail"].sudo().create(mail_values).send()

        return request.render("isic_website.page_contact", {"success": True, "error": {}})

    # ------------------------------------------------------------------
    # Redirect /actualites -> /blog
    # ------------------------------------------------------------------
    @http.route("/actualites", type="http", auth="public", website=True, sitemap=False)
    def actualites_redirect(self, **kw):
        return request.redirect("/blog", code=301)
