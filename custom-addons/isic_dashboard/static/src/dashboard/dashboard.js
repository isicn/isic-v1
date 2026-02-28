/** @odoo-module */

import { Component, onWillStart, useState } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DashboardChart } from "./chart/dashboard_chart";
import { KpiCard } from "./kpi_card/kpi_card";

export class IsicDashboard extends Component {
    static template = "isic_dashboard.Dashboard";
    static components = { KpiCard, DashboardChart };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: null,
            loading: true,
        });

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "isic.dashboard",
            "retrieve_dashboard",
            []
        );
        this.state.loading = false;
    }

    async onRefresh() {
        await this.loadDashboard();
    }

    onCardClick(actionXmlId) {
        this.action.doAction(actionXmlId);
    }
}

registry.category("actions").add("isic_dashboard.Dashboard", IsicDashboard);
