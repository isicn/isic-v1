// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
//
// Odoo 19 migration notes:
// - In Odoo 19, LinkPreview from "@mail/core/common/link_preview" is an OWL Component.
//   The imageUrl getter belongs to the LinkPreview Record model in
//   "@mail/core/common/link_preview_model" and only returns og_image or source_url
//   (Open Graph metadata). It does not reference attachments.
// - The attachment viewer functionality (defaultSource, downloadUrl, urlRoute) is now
//   handled by FileModelMixin in "@web/core/file_viewer/file_model", which Attachment
//   inherits from. DMS-specific URL routing is handled in attachment.esm.js.
// - This patch is no longer needed in Odoo 19.
