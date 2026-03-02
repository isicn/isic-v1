/** @odoo-module */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

// ==============================================================
//  1. Scroll Reveal — IntersectionObserver for fade-in on scroll
// ==============================================================

export class IsicScrollReveal extends Interaction {
    static selector = ".isic-www-reveal";

    start() {
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            this.el.classList.add("isic-www-reveal--visible");
            return;
        }
        this._observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("isic-www-reveal--visible");
                        this._observer.unobserve(entry.target);
                    }
                }
            },
            { threshold: 0.15 }
        );
        this._observer.observe(this.el);
    }

    destroy() {
        if (this._observer) {
            this._observer.disconnect();
        }
    }
}

registry.category("public.interactions").add("isic_website.scroll_reveal", IsicScrollReveal);

// ==============================================================
//  2. Counter Animation — animate numbers from 0 to data-target
// ==============================================================

export class IsicWwwCounterAnimation extends Interaction {
    static selector = ".isic-www-stat__value[data-target]";

    start() {
        this._target = parseInt(this.el.dataset.target, 10);
        this._suffix = this.el.dataset.suffix || "";
        if (isNaN(this._target) || this._target === 0) {
            this.el.textContent = "0" + this._suffix;
            return;
        }
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            this.el.textContent = this._target + this._suffix;
            return;
        }
        this._observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        this._animateCount(0, this._target, 800);
                        this._observer.unobserve(entry.target);
                    }
                }
            },
            { threshold: 0.3 }
        );
        this._observer.observe(this.el);
    }

    _animateCount(start, end, duration) {
        const startTime = performance.now();
        const step = (timestamp) => {
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            this.el.textContent = Math.floor(eased * (end - start) + start) + this._suffix;
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    }

    destroy() {
        if (this._observer) {
            this._observer.disconnect();
        }
    }
}

registry
    .category("public.interactions")
    .add("isic_website.counter_animation", IsicWwwCounterAnimation);

// ==============================================================
//  3. Sticky Header — transparent to opaque on scroll
// ==============================================================

export class IsicStickyHeader extends Interaction {
    static selector = "#wrapwrap";

    start() {
        this._header = document.querySelector("header#top");
        if (!this._header) {
            return;
        }
        this._onScroll = this._onScroll.bind(this);
        window.addEventListener("scroll", this._onScroll, { passive: true });
        this._onScroll();
    }

    _onScroll() {
        const scrolled = window.scrollY > 60;
        this._header.classList.toggle("isic-www-header--scrolled", scrolled);
    }

    destroy() {
        window.removeEventListener("scroll", this._onScroll);
    }
}

registry.category("public.interactions").add("isic_website.sticky_header", IsicStickyHeader);

// ==============================================================
//  4. Partners Carousel — auto-scroll logos
// ==============================================================

export class IsicPartnersCarousel extends Interaction {
    static selector = ".isic-www-partners-scroll";

    start() {
        // Duplicate logos for infinite scroll illusion
        const track = this.el.querySelector(".isic-www-partners-scroll__track");
        if (!track) {
            return;
        }
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            return;
        }
        const items = track.innerHTML;
        track.innerHTML = items + items;
    }
}

registry.category("public.interactions").add("isic_website.partners_carousel", IsicPartnersCarousel);

// ==============================================================
//  5. Timeline Scroll — animate timeline items on scroll
// ==============================================================

export class IsicTimelineScroll extends Interaction {
    static selector = ".isic-www-timeline";

    start() {
        const items = this.el.querySelectorAll(".isic-www-timeline__item");
        if (!items.length) {
            return;
        }
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            for (const item of items) {
                item.classList.add("isic-www-stagger--visible");
            }
            return;
        }
        this._observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("isic-www-stagger--visible");
                        this._observer.unobserve(entry.target);
                    }
                }
            },
            { threshold: 0.2 }
        );
        for (const item of items) {
            item.classList.add("isic-www-stagger");
            this._observer.observe(item);
        }
    }

    destroy() {
        if (this._observer) {
            this._observer.disconnect();
        }
    }
}

registry.category("public.interactions").add("isic_website.timeline_scroll", IsicTimelineScroll);

// ==============================================================
//  6. Stagger Container — sequential fade-in for child items
// ==============================================================

export class IsicWwwStaggerContainer extends Interaction {
    static selector = ".isic-www-stagger-container";

    start() {
        const items = this.el.querySelectorAll(".isic-www-stagger");
        if (!items.length) {
            return;
        }
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            for (const item of items) {
                item.classList.add("isic-www-stagger--visible");
            }
            return;
        }
        this._observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("isic-www-stagger--visible");
                        this._observer.unobserve(entry.target);
                    }
                }
            },
            { threshold: 0.1 }
        );
        for (const item of items) {
            this._observer.observe(item);
        }
    }

    destroy() {
        if (this._observer) {
            this._observer.disconnect();
        }
    }
}

registry
    .category("public.interactions")
    .add("isic_website.stagger_container", IsicWwwStaggerContainer);
