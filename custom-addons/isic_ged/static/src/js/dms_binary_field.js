/** @odoo-module */

import { BinaryField, binaryField } from "@web/views/fields/binary/binary_field";
import { registry } from "@web/core/registry";

/**
 * Custom binary field for DMS files.
 *
 * Overrides the default BinaryField to prevent auto-renaming when the
 * user uploads a replacement file. The standard widget overwrites the
 * filename field with the uploaded file's name, which is unexpected
 * when the user has already set a custom name.
 *
 * Behavior:
 *  - New record (name is empty): auto-set name from uploaded filename
 *  - Existing record (name already set): only update the binary content,
 *    keep the current name untouched
 */
export class DmsBinaryField extends BinaryField {
    update({ data, name }) {
        const { fileNameField, record } = this.props;
        const changes = { [this.props.name]: data || false };
        // Only auto-set name when it is currently empty (new upload)
        if (
            fileNameField &&
            fileNameField in record.fields &&
            !record.data[fileNameField]
        ) {
            changes[fileNameField] = name || "";
        }
        return this.props.record.update(changes);
    }
}

export const dmsBinaryField = {
    ...binaryField,
    component: DmsBinaryField,
};

registry.category("fields").add("dms_binary", dmsBinaryField);
