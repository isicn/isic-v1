/* Copyright 2021-2024 Tecnativa - Víctor Martínez
 * Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
//
// Odoo 19 migration notes:
// - In Odoo 19, _getCategoryDomain already pushes domain entries for active
//   categories (using "child_of" for hierarchical many2one, "=" otherwise).
//   The Odoo 18 version returned an empty array and the DMS patch added entries.
// - For DMS models, we need "=" instead of "child_of" to filter by the exact
//   selected directory, not its children. We override _getCategoryDomain to
//   replace the operator for DMS models, avoiding duplicate domain entries.

import {SearchModel} from "@web/search/search_model";
import {patch} from "@web/core/utils/patch";

patch(SearchModel.prototype, {
    _getCategoryDomain(excludedCategoryId) {
        if (!this.resModel || !this.resModel.startsWith("dms")) {
            return super._getCategoryDomain(...arguments);
        }

        // For DMS models, build the domain manually using "=" operator
        // instead of "child_of" to filter by exact directory.
        const domain = [];
        for (const category of this.categories) {
            if (category.id === excludedCategoryId || !category.activeValueId) {
                continue;
            }
            domain.push([category.fieldName, "=", category.activeValueId]);
        }

        // When no category is selected on dms.directory, filter for root directories
        // BUT skip this constraint when the user has an active text search so that
        // nested directories matching the query can appear in results.
        if (domain.length === 0 && this.resModel === "dms.directory") {
            const hasFieldSearch = this.query && this.query.some((facet) => {
                const item = this.searchItems[facet.searchItemId];
                return item && item.type === "field";
            });
            if (!hasFieldSearch) {
                for (const category of this.categories) {
                    if (category.id === excludedCategoryId) {
                        continue;
                    }
                    domain.push([category.fieldName, "=", false]);
                }
            }
        }

        return domain;
    },
});
