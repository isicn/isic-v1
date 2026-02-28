from odoo.tests.common import TransactionCase


class TestDashboard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dashboard = cls.env["isic.dashboard"]
        cls.Section = cls.env["isic.dashboard.section"]
        cls.AnneeAcademique = cls.env["isic.annee.academique"]

        # Use existing open year or create one
        cls.annee = cls.AnneeAcademique.search([("state", "=", "open")], limit=1)
        if not cls.annee:
            cls.annee = cls.AnneeAcademique.create(
                {
                    "code": "2025-2026-test",
                    "date_start": "2025-09-01",
                    "date_end": "2026-07-31",
                    "state": "open",
                }
            )

        cls.user_scolarite = cls.env["res.users"].create(
            {
                "name": "Agent Scolarité Test",
                "login": "scolarite_test_dashboard",
                "email": "scolarite_test_dashboard@isic.ac.ma",
                "group_ids": [
                    (4, cls.env.ref("isic_base.group_isic_scolarite").id),
                ],
            }
        )

        cls.user_enseignant = cls.env["res.users"].create(
            {
                "name": "Prof Test",
                "login": "prof_test_dashboard",
                "email": "prof_test_dashboard@isic.ac.ma",
                "group_ids": [
                    (4, cls.env.ref("isic_base.group_isic_enseignant").id),
                ],
            }
        )

        cls.user_direction = cls.env["res.users"].create(
            {
                "name": "Directeur Test",
                "login": "directeur_test_dashboard",
                "email": "directeur_test_dashboard@isic.ac.ma",
                "group_ids": [
                    (4, cls.env.ref("isic_base.group_isic_direction").id),
                ],
            }
        )

    # ------------------------------------------------------------------
    # Basic structure
    # ------------------------------------------------------------------

    def test_retrieve_dashboard_returns_data(self):
        """retrieve_dashboard returns a dict with expected keys."""
        data = self.Dashboard.retrieve_dashboard()
        self.assertIn("user_name", data)
        self.assertIn("annee_academique", data)
        self.assertIn("sections", data)
        self.assertIn("charts", data)
        self.assertIsInstance(data["sections"], list)
        self.assertIsInstance(data["charts"], list)

    def test_dashboard_annee_academique(self):
        """Dashboard shows the current academic year."""
        data = self.Dashboard.retrieve_dashboard()
        self.assertEqual(data["annee_academique"], self.annee.name)

    # ------------------------------------------------------------------
    # Section visibility by group
    # ------------------------------------------------------------------

    def test_direction_sees_overview(self):
        """Direction user sees the 'Vue d'ensemble' section."""
        data = self.Dashboard.with_user(self.user_direction).retrieve_dashboard()
        section_titles = [s["title"] for s in data["sections"]]
        self.assertIn("Vue d'ensemble", section_titles)

    def test_scolarite_sees_scolarite_section(self):
        """Scolarité user sees the 'Scolarité' section."""
        data = self.Dashboard.with_user(self.user_scolarite).retrieve_dashboard()
        section_titles = [s["title"] for s in data["sections"]]
        self.assertIn("Scolarité", section_titles)

    def test_enseignant_does_not_see_direction(self):
        """Enseignant does not see the direction overview."""
        data = self.Dashboard.with_user(self.user_enseignant).retrieve_dashboard()
        section_titles = [s["title"] for s in data["sections"]]
        self.assertNotIn("Vue d'ensemble", section_titles)

    def test_all_users_see_common_sections(self):
        """All internal users see Documents and Approbations."""
        for user in (self.user_enseignant, self.user_scolarite, self.user_direction):
            data = self.Dashboard.with_user(user).retrieve_dashboard()
            section_titles = [s["title"] for s in data["sections"]]
            self.assertIn("Documents", section_titles, f"Missing Documents for {user.name}")
            self.assertIn("Approbations", section_titles, f"Missing Approbations for {user.name}")

    def test_no_duplicate_sections(self):
        """Direction user doesn't get duplicate common sections."""
        data = self.Dashboard.with_user(self.user_direction).retrieve_dashboard()
        section_titles = [s["title"] for s in data["sections"]]
        self.assertEqual(section_titles.count("Documents"), 1)
        self.assertEqual(section_titles.count("Approbations"), 1)

    # ------------------------------------------------------------------
    # Active toggle
    # ------------------------------------------------------------------

    def test_inactive_section_hidden(self):
        """Archiving a section hides it from dashboard."""
        section_ged = self.Section.search([("code", "=", "ged")])
        section_ged.active = False
        try:
            data = self.Dashboard.with_user(self.user_enseignant).retrieve_dashboard()
            section_titles = [s["title"] for s in data["sections"]]
            self.assertNotIn("Documents", section_titles)
        finally:
            section_ged.active = True

    # ------------------------------------------------------------------
    # KPI structure
    # ------------------------------------------------------------------

    def test_kpi_structure(self):
        """Each KPI has the required keys."""
        data = self.Dashboard.retrieve_dashboard()
        for section in data["sections"]:
            self.assertIn("title", section)
            self.assertIn("kpis", section)
            for kpi in section["kpis"]:
                self.assertIn("label", kpi)
                self.assertIn("value", kpi)
                self.assertIn("icon", kpi)
                self.assertIn("color", kpi)
                self.assertIsInstance(kpi["value"], int)

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------

    def test_charts_returned(self):
        """retrieve_dashboard includes charts from sections with has_chart=True."""
        data = self.Dashboard.retrieve_dashboard()
        self.assertIsInstance(data["charts"], list)
        self.assertGreaterEqual(len(data["charts"]), 2)

    def test_chart_structure(self):
        """Each chart dict has title, type, and data with labels/datasets."""
        data = self.Dashboard.retrieve_dashboard()
        for chart in data["charts"]:
            self.assertIn("title", chart)
            self.assertIn("type", chart)
            self.assertIn("data", chart)
            self.assertIn("labels", chart["data"])
            self.assertIn("datasets", chart["data"])

    def test_direction_sees_line_chart(self):
        """Direction user sees the evolution line chart."""
        data = self.Dashboard.with_user(self.user_direction).retrieve_dashboard()
        chart_titles = [c["title"] for c in data["charts"]]
        self.assertIn("Évolution des demandes", chart_titles)

    def test_enseignant_no_line_chart(self):
        """Regular enseignant does not see the line chart."""
        data = self.Dashboard.with_user(self.user_enseignant).retrieve_dashboard()
        chart_titles = [c["title"] for c in data["charts"]]
        self.assertNotIn("Évolution des demandes", chart_titles)

    def test_chart_doughnut_has_five_states(self):
        """The doughnut chart has 5 state labels."""
        data = self.Dashboard.retrieve_dashboard()
        doughnut = next(c for c in data["charts"] if c["type"] == "doughnut")
        self.assertEqual(len(doughnut["data"]["labels"]), 5)
        self.assertEqual(len(doughnut["data"]["datasets"][0]["data"]), 5)

    # ------------------------------------------------------------------
    # Section ordering
    # ------------------------------------------------------------------

    def test_sections_ordered_by_sequence(self):
        """Sections appear in sequence order."""
        data = self.Dashboard.with_user(self.user_direction).retrieve_dashboard()
        # Direction sees: Vue d'ensemble (seq 10), Documents (seq 30), Approbations (seq 40)
        titles = [s["title"] for s in data["sections"]]
        if "Vue d'ensemble" in titles and "Documents" in titles:
            self.assertLess(titles.index("Vue d'ensemble"), titles.index("Documents"))
