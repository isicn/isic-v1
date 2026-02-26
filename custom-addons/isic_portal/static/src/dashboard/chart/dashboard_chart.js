/** @odoo-module */

import { Component, onWillStart, useRef, useEffect, onWillUnmount } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class DashboardChart extends Component {
    static template = "isic_portal.DashboardChart";
    static props = {
        title: String,
        type: String,
        data: Object,
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onWillStart(() => loadBundle("web.chartjs_lib"));

        useEffect(
            () => {
                this.renderChart();
                return () => this.destroyChart();
            },
            () => [this.props.data],
        );

        onWillUnmount(() => this.destroyChart());
    }

    renderChart() {
        this.destroyChart();
        if (this.canvasRef.el) {
            this.chart = new Chart(this.canvasRef.el, {
                type: this.props.type,
                data: this.props.data,
                options: this.getOptions(),
            });
        }
    }

    destroyChart() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    getOptions() {
        const isPie = ["pie", "doughnut"].includes(this.props.type);
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: isPie, position: "bottom" },
            },
            scales: isPie
                ? {}
                : {
                      y: { beginAtZero: true, ticks: { precision: 0 } },
                  },
        };
    }
}
