import logging
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, models

_logger = logging.getLogger(__name__)


class IsicPortalDashboard(models.AbstractModel):
    _name = "isic.portal.dashboard"
    _description = "Portail ISIC — Dashboard KPI"

    @api.model
    def retrieve_dashboard(self):
        """Return dashboard data adapted to the current user's groups."""
        user = self.env.user
        data = {
            "user_name": user.name,
            "sections": [],
        }

        # Année académique en cours
        annee = self.env["isic.annee.academique"]._get_current()
        data["annee_academique"] = annee.name if annee else ""

        # Build sections based on user groups
        if user.has_group("isic_base.group_isic_direction"):
            data["sections"].extend(self._section_direction(annee))
        if user.has_group("isic_base.group_isic_scolarite"):
            data["sections"].extend(self._section_scolarite(annee))

        # Sections available for all internal users
        data["sections"].extend(self._section_ged(annee))
        data["sections"].extend(self._section_approbation())

        # Charts
        data["charts"] = self._get_charts(annee)

        return data

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    @api.model
    def _section_direction(self, annee):
        """KPIs for Direction / top management."""
        Demande = self.env["isic.approbation.demande"]
        DmsFile = self.env["dms.file"]

        total_demandes = Demande.search_count([])
        pending_demandes = Demande.search_count([("state", "=", "submitted")])
        total_docs = DmsFile.search_count([])
        users_count = self.env["res.users"].search_count([("share", "=", False)])

        return [
            {
                "title": "Vue d'ensemble",
                "icon": "fa-tachometer",
                "kpis": [
                    {
                        "label": "Utilisateurs internes",
                        "value": users_count,
                        "icon": "fa-users",
                        "color": "primary",
                    },
                    {
                        "label": "Total documents GED",
                        "value": total_docs,
                        "icon": "fa-archive",
                        "color": "success",
                    },
                    {
                        "label": "Demandes en cours",
                        "value": pending_demandes,
                        "icon": "fa-hourglass-half",
                        "color": "warning",
                        "action": "isic_approbation.isic_approbation_demande_action_approve",
                    },
                    {
                        "label": "Total demandes",
                        "value": total_demandes,
                        "icon": "fa-check-circle",
                        "color": "info",
                        "action": "isic_approbation.isic_approbation_demande_action",
                    },
                ],
            },
        ]

    @api.model
    def _section_scolarite(self, annee):
        """KPIs for the academic affairs office."""
        Demande = self.env["isic.approbation.demande"]
        DmsFile = self.env["dms.file"]

        domain_annee = [("annee_academique_id", "=", annee.id)] if annee else []
        docs_draft = DmsFile.search_count([("ged_state", "=", "draft"), *domain_annee])
        docs_validated = DmsFile.search_count([("ged_state", "=", "validated"), *domain_annee])
        demandes_pending = Demande.search_count([("state", "=", "submitted")])

        return [
            {
                "title": "Scolarité",
                "icon": "fa-graduation-cap",
                "kpis": [
                    {
                        "label": "Documents à valider",
                        "value": docs_draft,
                        "icon": "fa-file-text-o",
                        "color": "warning",
                    },
                    {
                        "label": "Documents validés",
                        "value": docs_validated,
                        "icon": "fa-check-square-o",
                        "color": "success",
                    },
                    {
                        "label": "Demandes en attente",
                        "value": demandes_pending,
                        "icon": "fa-clock-o",
                        "color": "info",
                        "action": "isic_approbation.isic_approbation_demande_action_approve",
                    },
                ],
            },
        ]

    @api.model
    def _section_ged(self, annee):
        """GED section available to all internal users."""
        DmsFile = self.env["dms.file"]

        domain_annee = [("annee_academique_id", "=", annee.id)] if annee else []
        my_docs = DmsFile.search_count([("create_uid", "=", self.env.uid)])
        recent_docs = DmsFile.search_count(domain_annee)

        return [
            {
                "title": "Documents",
                "icon": "fa-folder-open",
                "kpis": [
                    {
                        "label": "Mes documents",
                        "value": my_docs,
                        "icon": "fa-file-o",
                        "color": "primary",
                    },
                    {
                        "label": "Documents cette année",
                        "value": recent_docs,
                        "icon": "fa-calendar",
                        "color": "info",
                    },
                ],
            },
        ]

    @api.model
    def _section_approbation(self):
        """Approval section available to all internal users."""
        Demande = self.env["isic.approbation.demande"]
        uid = self.env.uid

        my_total = Demande.search_count([("demandeur_id", "=", uid)])
        my_pending = Demande.search_count([("demandeur_id", "=", uid), ("state", "=", "submitted")])
        my_approved = Demande.search_count([("demandeur_id", "=", uid), ("state", "=", "approved")])
        to_approve = Demande.search_count([("reviewer_ids", "in", uid), ("state", "=", "submitted")])

        kpis = [
            {
                "label": "Mes demandes",
                "value": my_total,
                "icon": "fa-list",
                "color": "primary",
                "action": "isic_approbation.isic_approbation_demande_action_my",
            },
            {
                "label": "En attente",
                "value": my_pending,
                "icon": "fa-hourglass-half",
                "color": "warning",
            },
            {
                "label": "Approuvées",
                "value": my_approved,
                "icon": "fa-thumbs-up",
                "color": "success",
            },
        ]

        if to_approve:
            kpis.append(
                {
                    "label": "À approuver",
                    "value": to_approve,
                    "icon": "fa-gavel",
                    "color": "danger",
                    "action": "isic_approbation.isic_approbation_demande_action_approve",
                }
            )

        return [
            {
                "title": "Approbations",
                "icon": "fa-check-circle-o",
                "kpis": kpis,
            },
        ]

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------

    @api.model
    def _get_charts(self, annee):
        """Build chart data list based on user groups."""
        charts = [
            self._chart_demandes_by_state(),
            self._chart_docs_by_month(),
        ]
        user = self.env.user
        if user.has_group("isic_base.group_isic_direction") or user.has_group("isic_base.group_isic_scolarite"):
            charts.append(self._chart_demandes_by_month())
        return charts

    @api.model
    def _chart_demandes_by_state(self):
        """Doughnut: demandes par état."""
        Demande = self.env["isic.approbation.demande"]
        states = [
            ("draft", "Brouillon"),
            ("submitted", "Soumise"),
            ("approved", "Approuvée"),
            ("rejected", "Refusée"),
            ("cancelled", "Annulée"),
        ]
        colors = ["#0dcaf0", "#fd7e14", "#198754", "#dc3545", "#6c757d"]
        labels, values = [], []
        for code, label in states:
            labels.append(label)
            values.append(Demande.search_count([("state", "=", code)]))
        return {
            "title": "Demandes par état",
            "type": "doughnut",
            "data": {
                "labels": labels,
                "datasets": [{"data": values, "backgroundColor": colors}],
            },
        }

    @api.model
    def _chart_docs_by_month(self):
        """Bar: documents GED créés par mois (6 derniers mois)."""
        labels, values = self._aggregate_by_month("dms.file", 6)
        return {
            "title": "Documents par mois",
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Documents",
                        "data": values,
                        "backgroundColor": "#1B3A5C",
                    }
                ],
            },
        }

    @api.model
    def _chart_demandes_by_month(self):
        """Line: évolution des demandes par mois (6 derniers mois)."""
        labels, values = self._aggregate_by_month("isic.approbation.demande", 6)
        return {
            "title": "Évolution des demandes",
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Demandes",
                        "data": values,
                        "borderColor": "#D4A843",
                        "backgroundColor": "rgba(212, 168, 67, 0.15)",
                        "fill": True,
                    }
                ],
            },
        }

    @api.model
    def _aggregate_by_month(self, model_name, months):
        """Return (labels, values) for record counts grouped by month.

        Covers the last ``months`` months including the current one.
        Missing months are filled with 0.
        """
        today = date.today()
        first_day = today.replace(day=1) - relativedelta(months=months - 1)

        Model = self.env[model_name]
        domain = [("create_date", ">=", first_day.isoformat())]
        groups = Model._read_group(domain, groupby=["create_date:month"], aggregates=["__count"])

        # Build {(year, month): count} from _read_group results
        # create_date:month returns datetime.datetime truncated to 1st of month
        counts = {}
        for dt_val, count in groups:
            if dt_val:
                counts[(dt_val.year, dt_val.month)] = count

        month_names = [
            "",
            "jan.",
            "fév.",
            "mars",
            "avr.",
            "mai",
            "juin",
            "juil.",
            "août",
            "sep.",
            "oct.",
            "nov.",
            "déc.",
        ]
        labels, values = [], []
        for i in range(months):
            d = first_day + relativedelta(months=i)
            labels.append(f"{month_names[d.month]} {d.year}")
            values.append(counts.get((d.year, d.month), 0))
        return labels, values
