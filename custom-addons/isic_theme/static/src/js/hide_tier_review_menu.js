/** @odoo-module */

import { registry } from "@web/core/registry";

// Remove the redundant TierReviewMenu systray item from base_tier_validation.
// Pending reviews are already visible in the Activities menu.
const systrayRegistry = registry.category("systray");
if (systrayRegistry.contains("base_tier_validation.ReviewerMenu")) {
    systrayRegistry.remove("base_tier_validation.ReviewerMenu");
}
