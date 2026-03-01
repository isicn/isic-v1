/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

class PreviewField extends Component {
    static template = "isic_ged.PreviewField";
    static props = { ...standardFieldProps };

    get previewType() {
        return this.props.record.data.preview_type;
    }

    get previewUrl() {
        return `/isic_ged/preview/${this.props.record.resId}`;
    }

    get imageUrl() {
        return `/web/image/dms.file/${this.props.record.resId}/content`;
    }
}

registry.category("fields").add("preview_embed", PreviewField);
