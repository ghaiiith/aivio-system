/** @odoo-module **/
// Copyright (C) 2026 aivio_enterprise_theme
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import { registry } from "@web/core/registry";

function escapeHTML(value) {
    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function normalize(value) {
    return String(value || "").trim().toLowerCase();
}

const aivioResponsiveEnhancementService = {
    dependencies: ["menu"],
    start(env, { menu }) {
        const getAppByNode = (node) => {
            const section = Number(node.dataset.section || 0);
            const xmlid = node.dataset.menuXmlid || node.getAttribute("data-menu-xmlid") || "";
            const label = normalize(node.textContent);
            const apps = menu.getApps ? menu.getApps() : [];
            return (
                apps.find((app) => section && app.id === section) ||
                apps.find((app) => xmlid && app.xmlid === xmlid) ||
                apps.find((app) => normalize(app.name) === label)
            );
        };

        const iconMarkup = (app, label) => {
            const safeLabel = escapeHTML(app?.name || label || "App");
            if (app?.webIconData) {
                return `<span class="o_aivio_et_app_icon"><img src="${escapeHTML(app.webIconData)}" alt="${safeLabel}" loading="lazy"/></span>`;
            }
            return `<span class="o_aivio_et_app_icon o_aivio_et_app_icon_letter">${safeLabel.charAt(0).toUpperCase() || "?"}</span>`;
        };

        const enhanceNativeAppsMenu = (container) => {
            if (!container || container.classList.contains("o_aivio_native_apps_enhanced")) {
                return;
            }
            const appItems = [...container.querySelectorAll("a.o_app, button.o_app, .o_app[href]")];
            if (!appItems.length) {
                return;
            }
            container.classList.add("o_aivio_native_apps_enhanced");

            const searchWrap = document.createElement("div");
            searchWrap.className = "o_aivio_native_apps_search_wrap";
            searchWrap.innerHTML = `<input class="o_aivio_native_apps_search" type="search" autocomplete="off" placeholder="Search apps..."/>`;
            container.prepend(searchWrap);

            for (const item of appItems) {
                if (item.dataset.aivioEnhanced === "1") {
                    continue;
                }
                const app = getAppByNode(item);
                const label = (app?.name || item.textContent || "").trim();
                item.dataset.aivioEnhanced = "1";
                item.innerHTML = `${iconMarkup(app, label)}<span class="o_aivio_et_app_label">${escapeHTML(label)}</span>`;
            }

            const input = searchWrap.querySelector("input");
            input.addEventListener("input", () => {
                const term = normalize(input.value);
                for (const item of appItems) {
                    const text = normalize(item.textContent);
                    item.classList.toggle("d-none", Boolean(term) && !text.includes(term));
                }
            });
            setTimeout(() => input.focus({ preventScroll: true }), 30);
        };

        const scan = () => {
            const candidates = document.querySelectorAll(
                ".o_navbar_apps_menu .dropdown-menu, .o_navbar_apps_menu .o-dropdown--menu, .o_navbar_apps_menu .o_popover, .o_aivio_enterprise_apps_popover"
            );
            for (const candidate of candidates) {
                enhanceNativeAppsMenu(candidate);
            }
        };

        const observer = new MutationObserver(scan);
        observer.observe(document.body, { childList: true, subtree: true });
        document.addEventListener("click", () => setTimeout(scan, 0), true);

        // Keyboard support for the AIVIO home grid: arrow keys move between apps, Enter opens.
        document.addEventListener("keydown", (ev) => {
            const homeRoot = document.querySelector(".o_aivio_enterprise_home_menu:not([hidden])");
            if (!homeRoot) {
                return;
            }
            const apps = [...homeRoot.querySelectorAll(".o_aivio_home_app:not(.d-none)")];
            if (!apps.length) {
                return;
            }
            const currentIndex = apps.indexOf(document.activeElement);
            const columns = window.matchMedia("(max-width: 575.98px)").matches
                ? 3
                : window.matchMedia("(max-width: 991.98px)").matches
                ? 4
                : 6;
            let nextIndex = currentIndex;
            if (["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp"].includes(ev.key)) {
                ev.preventDefault();
                if (ev.key === "ArrowRight") {
                    nextIndex = currentIndex < 0 ? 0 : Math.min(apps.length - 1, currentIndex + 1);
                } else if (ev.key === "ArrowLeft") {
                    nextIndex = currentIndex < 0 ? 0 : Math.max(0, currentIndex - 1);
                } else if (ev.key === "ArrowDown") {
                    nextIndex = currentIndex < 0 ? 0 : Math.min(apps.length - 1, currentIndex + columns);
                } else if (ev.key === "ArrowUp") {
                    nextIndex = currentIndex < 0 ? 0 : Math.max(0, currentIndex - columns);
                }
                apps[nextIndex]?.focus();
            }
        });

        env.bus.addEventListener("AIVIO:HOME_MENU:SHOW", () => setTimeout(scan, 0));
        return { scan };
    },
};

registry.category("services").add("aivio_enterprise_theme.responsive_enhancements", aivioResponsiveEnhancementService);
