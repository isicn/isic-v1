// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
//
// Odoo 19 migration notes:
// - In Odoo 19, LinkPreview from "@mail/core/common/link_preview" is an OWL Component,
//   NOT a model/record. The imageUrl getter is on the LinkPreview Record model in
//   "@mail/core/common/link_preview_model".
// - The LinkPreview model's imageUrl simply returns og_image or source_url and has
//   nothing to do with attachments. This patch was originally designed for Odoo 18
//   where the architecture was different.
// - Since the LinkPreview model in Odoo 19 doesn't reference attachments at all
//   (it only deals with Open Graph metadata from URLs), this patch is no longer
//   needed. DMS file content URLs are now handled by the attachment.esm.js patch
//   which overrides urlRoute/urlQueryParams on the Attachment model.
