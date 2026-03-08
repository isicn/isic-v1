import re

import odoo.tests


@odoo.tests.tagged("post_install", "-at_install")
class TestIsicWebsiteRoutes(odoo.tests.HttpCase):
    """Test all ISIC website public routes return 200."""

    def _get_csrf_token(self):
        """GET /contact and extract CSRF token from the HTML form."""
        resp = self.url_open("/contact", timeout=30)
        match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)', resp.text)
        return match.group(1) if match else ""

    # ------------------------------------------------------------------
    # Static pages (public, auth="public")
    # ------------------------------------------------------------------
    def test_homepage(self):
        """Homepage / returns 200."""
        response = self.url_open("/", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_institut(self):
        """/institut returns 200."""
        response = self.url_open("/institut", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_formations(self):
        """/formations returns 200."""
        response = self.url_open("/formations", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_vie_etudiante(self):
        """/vie-etudiante returns 200."""
        response = self.url_open("/vie-etudiante", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_recherche(self):
        """/recherche returns 200."""
        response = self.url_open("/recherche", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        """/contact returns 200."""
        response = self.url_open("/contact", timeout=30)
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Redirect: /actualites → /blog (301)
    # ------------------------------------------------------------------
    def test_actualites_redirects_to_blog(self):
        """/actualites redirects to /blog with 301."""
        response = self.url_open("/actualites", timeout=30, allow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertIn("/blog", response.headers.get("Location", ""))

    # ------------------------------------------------------------------
    # Homepage content
    # ------------------------------------------------------------------
    def test_homepage_contains_isic(self):
        """Homepage contains ISIC branding."""
        response = self.url_open("/", timeout=30)
        # Page should mention ISIC somewhere
        self.assertIn(b"ISIC", response.content)

    def test_homepage_contains_1969(self):
        """Homepage mentions founding year 1969."""
        response = self.url_open("/", timeout=30)
        self.assertIn(b"1969", response.content)

    # ------------------------------------------------------------------
    # Contact form: POST /contact/submit
    # ------------------------------------------------------------------
    def test_contact_submit_success(self):
        """Valid contact form submission returns success."""
        csrf = self._get_csrf_token()
        response = self.url_open(
            "/contact/submit",
            data={
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Test subject",
                "message": "This is a test message",
                "csrf_token": csrf,
            },
            timeout=30,
        )
        self.assertEqual(response.status_code, 200)

    def test_contact_submit_missing_name(self):
        """Contact form without name re-renders with error."""
        csrf = self._get_csrf_token()
        response = self.url_open(
            "/contact/submit",
            data={
                "name": "",
                "email": "test@example.com",
                "message": "A message",
                "csrf_token": csrf,
            },
            timeout=30,
        )
        self.assertEqual(response.status_code, 200)

    def test_contact_submit_missing_email(self):
        """Contact form without email re-renders with error."""
        csrf = self._get_csrf_token()
        response = self.url_open(
            "/contact/submit",
            data={
                "name": "Test",
                "email": "",
                "message": "A message",
                "csrf_token": csrf,
            },
            timeout=30,
        )
        self.assertEqual(response.status_code, 200)

    def test_contact_submit_missing_message(self):
        """Contact form without message re-renders with error."""
        csrf = self._get_csrf_token()
        response = self.url_open(
            "/contact/submit",
            data={
                "name": "Test",
                "email": "test@example.com",
                "message": "",
                "csrf_token": csrf,
            },
            timeout=30,
        )
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Institut sub-content
    # ------------------------------------------------------------------
    def test_institut_contains_professeurs(self):
        """/institut page contains professor data."""
        response = self.url_open("/institut", timeout=30)
        # Should mention at least one known professor
        self.assertIn(b"Bensfia", response.content)

    # ------------------------------------------------------------------
    # Formations content
    # ------------------------------------------------------------------
    def test_formations_contains_licence(self):
        """/formations mentions Licence."""
        response = self.url_open("/formations", timeout=30)
        self.assertIn(b"Licence", response.content)

    def test_formations_contains_master(self):
        """/formations mentions Master."""
        response = self.url_open("/formations", timeout=30)
        self.assertIn(b"Master", response.content)

    # ------------------------------------------------------------------
    # Recherche content
    # ------------------------------------------------------------------
    def test_recherche_contains_partenaires(self):
        """/recherche mentions partenaires."""
        response = self.url_open("/recherche", timeout=30)
        content = response.content.lower()
        self.assertIn(b"partenaire", content)
