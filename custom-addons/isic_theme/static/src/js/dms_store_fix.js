/** @odoo-module **/

/**
 * Fix DMS module compatibility with Odoo 19 mail store.
 *
 * In Odoo 19, mail store models are keyed by their Python _name
 * (e.g. store["ir.attachment"]), but the DMS module uses the old
 * pattern (store.Attachment). This service adds backward-compatible
 * aliases on the mail store so DMS works without modification.
 */
import { registry } from "@web/core/registry";

const dmsStoreFix = {
    dependencies: ["mail.store"],
    start(env, services) {
        const store = services["mail.store"];
        if (store && store["ir.attachment"] && !store.Attachment) {
            store.Attachment = store["ir.attachment"];
        }
    },
};

registry.category("services").add("isic_theme.dms_store_fix", dmsStoreFix);
