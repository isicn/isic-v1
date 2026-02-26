/** @odoo-module */

import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "isic_portal.KpiCard";
    static props = {
        label: String,
        value: Number,
        icon: { type: String, optional: true },
        color: { type: String, optional: true },
        action: { type: String, optional: true },
        onCardClick: { type: Function, optional: true },
    };
    static defaultProps = {
        icon: "fa-bar-chart",
        color: "primary",
    };

    get colorClass() {
        return `isic-kpi-card--${this.props.color}`;
    }

    onKpiClick() {
        if (this.props.action && this.props.onCardClick) {
            this.props.onCardClick(this.props.action);
        }
    }
}
