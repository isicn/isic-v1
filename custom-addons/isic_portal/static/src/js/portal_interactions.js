/** @odoo-module */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

// ==============================================================
//  1. Counter Animation — animate stat numbers from 0 to target
// ==============================================================

export class IsicCounterAnimation extends Interaction {
    static selector = ".isic-stat-card__value[data-target]";

    start() {
        const target = parseInt(this.el.dataset.target, 10);
        if (isNaN(target) || target === 0) {
            this.el.textContent = "0";
            return;
        }
        this._animateCount(0, target, 600);
    }

    _animateCount(start, end, duration) {
        const startTime = performance.now();
        const step = (timestamp) => {
            const progress = Math.min((timestamp - startTime) / duration, 1);
            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            this.el.textContent = Math.floor(eased * (end - start) + start);
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    }
}

registry
    .category("public.interactions")
    .add("isic_portal.counter_animation", IsicCounterAnimation);

// ==============================================================
//  2. Category Selector — click to select category cards
// ==============================================================

export class IsicCategorySelector extends Interaction {
    static selector = ".isic-category-grid";

    dynamicContent = {
        ".isic-category-card": {
            "t-on-click": this.onCardClick,
        },
    };

    setup() {
        this.hiddenInput = this.el.querySelector('input[name="categorie_id"]');
    }

    onCardClick(ev) {
        const card = ev.currentTarget;
        const catId = card.dataset.categoryId;
        // Deselect all
        for (const c of this.el.querySelectorAll(".isic-category-card")) {
            c.classList.remove("isic-category-card--selected");
        }
        // Select clicked
        card.classList.add("isic-category-card--selected");
        if (this.hiddenInput) {
            this.hiddenInput.value = catId;
        }
    }
}

registry
    .category("public.interactions")
    .add("isic_portal.category_selector", IsicCategorySelector);

// ==============================================================
//  3. Drop Zone — drag-and-drop file upload
// ==============================================================

export class IsicDropZone extends Interaction {
    static selector = ".isic-drop-zone";

    dynamicContent = {
        _root: {
            "t-on-dragover.prevent": this.onDragOver,
            "t-on-dragleave": this.onDragLeave,
            "t-on-drop.prevent": this.onDrop,
            "t-on-click": this.onClick,
        },
        ".isic-drop-zone__clear": {
            "t-on-click.stop": this.onClear,
        },
    };

    setup() {
        this.fileInput = this.el.querySelector(".isic-drop-zone__input");
        this.fileNameEl = this.el.querySelector(".isic-drop-zone__filename");
        if (this.fileInput) {
            this.fileInput.addEventListener("change", () => {
                if (this.fileInput.files.length) {
                    this._showFileName(this.fileInput.files[0].name);
                }
            });
        }
    }

    onDragOver() {
        this.el.classList.add("isic-drop-zone--active");
    }

    onDragLeave() {
        this.el.classList.remove("isic-drop-zone--active");
    }

    onDrop(ev) {
        this.el.classList.remove("isic-drop-zone--active");
        const files = ev.dataTransfer.files;
        if (files.length && this.fileInput) {
            this.fileInput.files = files;
            this._showFileName(files[0].name);
        }
    }

    onClick() {
        if (this.fileInput) {
            this.fileInput.click();
        }
    }

    onClear() {
        if (this.fileInput) {
            this.fileInput.value = "";
        }
        if (this.fileNameEl) {
            this.fileNameEl.textContent = "";
        }
        this.el.classList.remove("isic-drop-zone--has-file");
    }

    _showFileName(name) {
        if (this.fileNameEl) {
            this.fileNameEl.textContent = name;
        }
        this.el.classList.add("isic-drop-zone--has-file");
    }
}

registry
    .category("public.interactions")
    .add("isic_portal.drop_zone", IsicDropZone);

// ==============================================================
//  4. Stagger Trigger — IntersectionObserver for fade-in
// ==============================================================

export class IsicStaggerTrigger extends Interaction {
    static selector = ".isic-stagger-container";

    start() {
        const items = this.el.querySelectorAll(".isic-stagger-item");
        if (!items.length) {
            return;
        }
        // If prefers-reduced-motion, show immediately
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            for (const item of items) {
                item.classList.add("isic-stagger-item--visible");
            }
            return;
        }
        const observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("isic-stagger-item--visible");
                        observer.unobserve(entry.target);
                    }
                }
            },
            { threshold: 0.1 }
        );
        for (const item of items) {
            observer.observe(item);
        }
    }
}

registry
    .category("public.interactions")
    .add("isic_portal.stagger_trigger", IsicStaggerTrigger);
