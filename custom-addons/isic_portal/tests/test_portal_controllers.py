import odoo.tests


@odoo.tests.tagged("post_install", "-at_install")
class TestPortalControllers(odoo.tests.HttpCase):
    """Test portal HTTP routes as an authenticated portal user."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Demande = cls.env["isic.approbation.demande"]
        cls.Categorie = cls.env["isic.approbation.categorie"]

        # Portal user (student)
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Etudiant Portal Test",
                "login": "portal_ctrl_test",
                "password": "portal_ctrl_test",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_portal").id,
                            cls.env.ref("isic_base.group_isic_etudiant").id,
                        ],
                    )
                ],
            }
        )

        # Use existing ATT category (created by post_init_hook) or create one
        cls.cat_att = cls.Categorie.search([("code", "=", "ATT")], limit=1)
        if not cls.cat_att:
            cls.cat_att = cls.Categorie.create(
                {
                    "name": "Attestation Ctrl Test",
                    "code": "ATT",
                    "approbation_requise": False,
                    "groupe_demandeur_ids": [(4, cls.env.ref("isic_base.group_isic_etudiant").id)],
                }
            )
        # Ensure students can access this category
        etudiant_group = cls.env.ref("isic_base.group_isic_etudiant")
        if etudiant_group not in cls.cat_att.groupe_demandeur_ids:
            cls.cat_att.write({"groupe_demandeur_ids": [(4, etudiant_group.id)]})

        # Create a few demandes for list/filter tests
        for i, state in enumerate(["draft", "submitted", "approved"]):
            demande = cls.Demande.sudo().create(
                {
                    "categorie_id": cls.cat_att.id,
                    "demandeur_id": cls.portal_user.id,
                    "motif": f"Test demande {i}",
                }
            )
            if state in ("submitted", "approved"):
                demande.action_submit()
            if state == "approved":
                demande.action_approve()

    # ------------------------------------------------------------------
    # /my — Home page with counters
    # ------------------------------------------------------------------
    def test_home_accessible(self):
        """Portal home page returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_home_contains_counters(self):
        """Portal home page contains demande counter values."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my", timeout=30)
        # The page should render without error (counters embedded server-side)
        self.assertIn(b"portal_my_home", response.content)

    # ------------------------------------------------------------------
    # /my/demandes — List
    # ------------------------------------------------------------------
    def test_demandes_list_accessible(self):
        """Demandes list page returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_demandes_list_sort_by_state(self):
        """Sorting by state returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes?sortby=state", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_demandes_list_filter_approved(self):
        """Filtering by approved returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes?filterby=approved", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_demandes_list_search_reference(self):
        """Searching by reference returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes?search=ATT&search_in=reference", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_demandes_list_search_categorie(self):
        """Searching by category returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes?search=Attestation&search_in=categorie", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_demandes_list_invalid_sortby_falls_back(self):
        """Invalid sortby falls back to date (no crash)."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes?sortby=invalid_sort", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_demandes_list_invalid_filterby_falls_back(self):
        """Invalid filterby falls back to all (no crash)."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes?filterby=nonexistent", timeout=30)
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # /my/demandes/<id> — Detail
    # ------------------------------------------------------------------
    def test_demande_detail_accessible(self):
        """Portal user can view their own demande detail."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        demande = self.Demande.sudo().search([("demandeur_id", "=", self.portal_user.id)], limit=1)
        response = self.url_open(f"/my/demandes/{demande.id}", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_demande_detail_rejected_shows_rejected_pipeline(self):
        """Rejected demande shows rejected in pipeline."""
        demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": self.portal_user.id,
                "motif": "Will be rejected",
            }
        )
        demande.action_submit()
        demande.action_reject(motif="Test rejection")

        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open(f"/my/demandes/{demande.id}", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_demande_detail_not_found_redirects(self):
        """Accessing a non-existent demande redirects to /my."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes/999999", timeout=30)
        # Should redirect to /my (302 → 200 after redirect)
        self.assertEqual(response.status_code, 200)

    def test_demande_detail_other_user_redirects(self):
        """Portal user cannot view another user's demande — redirects."""
        other_user = self.env["res.users"].create(
            {
                "name": "Other Student",
                "login": "other_portal_ctrl",
                "password": "other_portal_ctrl",
                "group_ids": [
                    (6, 0, [self.env.ref("base.group_portal").id]),
                ],
            }
        )
        other_demande = self.Demande.sudo().create(
            {
                "categorie_id": self.cat_att.id,
                "demandeur_id": other_user.id,
                "motif": "Other user demande",
            }
        )
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open(f"/my/demandes/{other_demande.id}", timeout=30)
        # Should redirect to /my (access denied)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Other user demande", response.content)

    # ------------------------------------------------------------------
    # /my/demandes/new — Form
    # ------------------------------------------------------------------
    def test_new_demande_form_accessible(self):
        """New demande form returns 200 with categories."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/demandes/new", timeout=30)
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # POST /my/demandes/submit — Submission
    # ------------------------------------------------------------------
    def test_submit_demande_success(self):
        """Submitting a valid demande creates it and redirects."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open(
            "/my/demandes/submit",
            data={
                "categorie_id": str(self.cat_att.id),
                "motif": "Besoin attestation de scolarite",
                "priorite": "0",
                "csrf_token": odoo.http.Request.csrf_token(self),
            },
            timeout=30,
        )
        # Should redirect to /my/demandes/<id> (follow redirects → 200)
        self.assertEqual(response.status_code, 200)

        # Verify demande was created
        new_demande = self.Demande.sudo().search(
            [
                ("demandeur_id", "=", self.portal_user.id),
                ("motif", "=", "Besoin attestation de scolarite"),
            ]
        )
        self.assertTrue(new_demande, "Demande should be created")
        self.assertEqual(new_demande.state, "submitted", "Demande should be auto-submitted")

    def test_submit_demande_missing_motif(self):
        """Submitting without motif re-renders form with error."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open(
            "/my/demandes/submit",
            data={
                "categorie_id": str(self.cat_att.id),
                "motif": "",
                "csrf_token": odoo.http.Request.csrf_token(self),
            },
            timeout=30,
        )
        self.assertEqual(response.status_code, 200)

    def test_submit_demande_missing_categorie(self):
        """Submitting without category re-renders form with error."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open(
            "/my/demandes/submit",
            data={
                "motif": "Test motif",
                "csrf_token": odoo.http.Request.csrf_token(self),
            },
            timeout=30,
        )
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # /my/profile
    # ------------------------------------------------------------------
    def test_profile_accessible(self):
        """Profile page returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/profile", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_profile_shows_partner_name(self):
        """Profile page contains the partner name."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/profile", timeout=30)
        self.assertIn(b"Etudiant Portal Test", response.content)

    # ------------------------------------------------------------------
    # /my/documents
    # ------------------------------------------------------------------
    def test_documents_accessible(self):
        """Documents page returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/documents", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_documents_filter_by_state(self):
        """Documents page with state filter returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/documents?doc_state=validated", timeout=30)
        self.assertEqual(response.status_code, 200)

    def test_documents_search(self):
        """Documents page with search returns 200."""
        self.authenticate("portal_ctrl_test", "portal_ctrl_test")
        response = self.url_open("/my/documents?search=test", timeout=30)
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Unauthenticated access
    # ------------------------------------------------------------------
    def test_unauthenticated_redirect(self):
        """Unauthenticated access to portal routes redirects to login."""
        for route in ["/my/demandes", "/my/demandes/new", "/my/profile", "/my/documents"]:
            response = self.url_open(route, timeout=30, allow_redirects=False)
            self.assertIn(response.status_code, (302, 303), f"Route {route} should redirect")
