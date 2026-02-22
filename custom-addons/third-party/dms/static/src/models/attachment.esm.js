// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
//
// Odoo 19 migration notes:
// - defaultSource, downloadUrl, urlRoute, urlQueryParams are now in FileModelMixin
//   (@web/core/file_viewer/file_model), inherited by Attachment via FileModelMixin(Record).
// - _handleImage, _handlePdf, _handleYoutube no longer exist on Attachment.
// - We override urlRoute and urlQueryParams to redirect DMS file content
//   through the correct controller endpoint.
import {Attachment} from "@mail/core/common/attachment_model";
import {patch} from "@web/core/utils/patch";

patch(Attachment.prototype, {
    /**
     * Override urlRoute to serve DMS file content from the dms.file model
     * instead of ir.attachment. For non-DMS attachments, fall back to the
     * default FileModelMixin behaviour.
     */
    get urlRoute() {
        if (this.model_name && this.model_name === "dms.file") {
            return `/web/content`;
        }
        return super.urlRoute;
    },

    /**
     * Override urlQueryParams to pass model/field info for DMS files.
     */
    get urlQueryParams() {
        if (this.model_name && this.model_name === "dms.file") {
            return {
                id: this.id,
                field: "content",
                model: "dms.file",
                filename_field: "name",
            };
        }
        return super.urlQueryParams;
    },
});
