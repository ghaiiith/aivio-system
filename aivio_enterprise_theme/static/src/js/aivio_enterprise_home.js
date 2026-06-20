/** @odoo-module **/
// Copyright (C) 2026 aivio_enterprise_theme
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";

const HOME_OPEN_CLASS = "o_aivio_home_menu_open";
const HOME_ROOT_CLASS = "o_aivio_enterprise_home_menu";

/**
 * Odoo Community normally opens the first root application when /odoo has no
 * explicit action. In many databases that first app is Discuss. Enterprise
 * opens a Home Menu instead. This patch changes the Community fallback so the
 * backend lands on the AIVIO Enterprise-style home menu, not on Discuss.
 */
patch(WebClient.prototype, {
    _loadDefaultApp() {
        this.env.bus.trigger("AIVIO:HOME_MENU:SHOW", { source: "default_app" });
        try {
            this.title.setParts({ action: "Home" });
        } catch (error) {
            // Keep the webclient usable if the title service changes upstream.
        }
        return Promise.resolve(true);
    },
});

function escapeHTML(value) {
    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function getActionHref(app) {
    const actionPath = app.actionPath || (app.actionID ? `action-${app.actionID}` : "");
    return actionPath ? `/odoo/${actionPath}` : "/odoo";
}

function appIconMarkup(app) {
    const name = app.name || "";
    if (app.webIconData) {
        return `
            <span class="o_aivio_home_app_icon">
                <img src="${escapeHTML(app.webIconData)}" alt="${escapeHTML(name)}" loading="lazy" />
            </span>`;
    }
    return `
        <span class="o_aivio_home_app_icon o_aivio_home_app_icon_letter">
            ${escapeHTML(name ? name[0].toUpperCase() : "?")}
        </span>`;
}

const aivioEnterpriseHomeService = {
    dependencies: ["menu"],
    start(env, { menu }) {
        let root;
        let isOpen = false;

        function ensureRoot() {
            if (root && document.body.contains(root)) {
                return root;
            }
            root = document.createElement("div");
            root.className = HOME_ROOT_CLASS;
            root.setAttribute("aria-label", "AIVIO Home Menu");
            root.setAttribute("role", "navigation");
            root.hidden = true;
            document.body.appendChild(root);
            return root;
        }

        function getApps() {
            try {
                const apps = menu.getApps() || [];
                const bottomXmlIds = new Set([
                    "base.menu_management",
                    "base.menu_administration",
                    "base.menu_custom",
                ]);
                const normal = [];
                const bottom = [];
                for (const app of apps) {
                    if (bottomXmlIds.has(app.xmlid || "")) {
                        bottom.push(app);
                    } else {
                        normal.push(app);
                    }
                }
                return [...normal, ...bottom];
            } catch (error) {
                return [];
            }
        }

        function render() {
            const apps = getApps();
            const appCards = apps
                .map((app) => `
                    <a href="${escapeHTML(getActionHref(app))}"
                       class="o_aivio_home_app"
                       tabindex="0"
                       data-menu-id="${escapeHTML(app.id)}"
                       data-menu-xmlid="${escapeHTML(app.xmlid || "")}">
                        ${appIconMarkup(app)}
                        <span class="o_aivio_home_app_label">${escapeHTML(app.name)}</span>
                    </a>`)
                .join("");

            ensureRoot().innerHTML = `
                <div class="o_aivio_home_background"></div>
                <div class="o_aivio_home_content">
                    <div class="o_aivio_home_search_wrap">
                        <input class="o_aivio_home_search" type="search" placeholder="Search apps..." autocomplete="off" aria-label="Search apps" />
                    </div>
                    <div class="o_aivio_home_apps_grid">
                        ${appCards}
                    </div>
                    <div class="o_aivio_home_no_results d-none">No apps found</div>
                    <div class="o_aivio_home_footer">© ${new Date().getFullYear()} aivio_enterprise_theme</div>
                </div>`;
        }

        function showHome() {
            render();
            ensureRoot().hidden = false;
            document.body.classList.add(HOME_OPEN_CLASS);
            isOpen = true;
            const search = root.querySelector(".o_aivio_home_search");
            if (search) {
                setTimeout(() => search.focus({ preventScroll: true }), 50);
            }
        }

        function hideHome() {
            if (!root) {
                return;
            }
            root.hidden = true;
            document.body.classList.remove(HOME_OPEN_CLASS);
            isOpen = false;
        }

        function filterApps(term) {
            const normalizedTerm = (term || "").trim().toLowerCase();
            const cards = root ? [...root.querySelectorAll(".o_aivio_home_app")] : [];
            let visibleCount = 0;
            for (const card of cards) {
                const label = (card.textContent || "").toLowerCase();
                const hidden = Boolean(normalizedTerm) && !label.includes(normalizedTerm);
                card.classList.toggle("d-none", hidden);
                if (!hidden) {
                    visibleCount += 1;
                }
            }
            const noResults = root?.querySelector(".o_aivio_home_no_results");
            noResults?.classList.toggle("d-none", visibleCount !== 0);
        }

        env.bus.addEventListener("AIVIO:HOME_MENU:SHOW", showHome);
        env.bus.addEventListener("ACTION_MANAGER:UI-UPDATED", hideHome);
        env.bus.addEventListener("MENUS:APP-CHANGED", () => {
            if (isOpen) {
                render();
            }
        });

        document.addEventListener(
            "click",
            async (ev) => {
                const homeButton = ev.target.closest(
                    ".o_navbar_apps_menu button[title='Home Menu'], .o_menu_toggle[accesskey='h']"
                );
                if (homeButton && !window.matchMedia("(max-width: 767.98px)").matches) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    ev.stopImmediatePropagation();
                    showHome();
                    return;
                }

                const appLink = ev.target.closest(`.${HOME_ROOT_CLASS} .o_aivio_home_app`);
                if (appLink) {
                    ev.preventDefault();
                    const menuId = Number(appLink.dataset.menuId || 0);
                    const selectedMenu = menuId ? menu.getMenu(menuId) : null;
                    if (selectedMenu) {
                        hideHome();
                        await menu.selectMenu(selectedMenu);
                    }
                }
            },
            true
        );

        document.addEventListener("input", (ev) => {
            if (ev.target.matches(`.${HOME_ROOT_CLASS} .o_aivio_home_search`)) {
                filterApps(ev.target.value);
            }
        });

        document.addEventListener("keydown", (ev) => {
            if (!isOpen) {
                return;
            }
            if (ev.key === "Escape") {
                hideHome();
            }
            if (ev.key === "h" && (ev.altKey || ev.ctrlKey || ev.metaKey)) {
                showHome();
            }
        });

        return {
            show: showHome,
            hide: hideHome,
            isOpen: () => isOpen,
        };
    },
};

registry.category("services").add("aivio_enterprise_theme.home_menu", aivioEnterpriseHomeService);
