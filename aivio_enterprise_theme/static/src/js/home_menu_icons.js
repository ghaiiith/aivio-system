/** @odoo-module **/
// Copyright (C) 2026 aivio_enterprise_theme
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import { registry } from "@web/core/registry";

/**
 * Adds Enterprise-like icons to the normal Odoo Community Apps Menu.
 *
 * This is intentionally a UI layer only: navigation, menu permissions, and
 * active app behavior remain the original Odoo web behavior.
 */
const aivioHomeMenuIconsService = {
    dependencies: ["menu"],
    start(env, { menu }) {
        function getAppData() {
            const iconsByID = {};
            const endMenuIDs = new Set();
            try {
                const apps = menu.getApps();
                for (const app of apps) {
                    const id = String(app.id);
                    iconsByID[id] = {
                        icon: app.webIconData || false,
                        name: app.name || "",
                        xmlid: app.xmlid || "",
                    };
                    if (["base.menu_management", "base.menu_administration", "base.menu_custom"].includes(app.xmlid || "")) {
                        endMenuIDs.add(id);
                    }
                }
            } catch (error) {
                // Keep the backend usable even if a custom menu provider fails.
            }
            return { iconsByID, endMenuIDs };
        }

        function findAppsPopover(root) {
            if (!root || root.nodeType !== 1) {
                return null;
            }
            if (root.matches && root.matches(".o_popover, .dropdown-menu, .o-dropdown--menu")) {
                return root.querySelector("a.o_app") ? root : null;
            }
            if (root.querySelector) {
                const popovers = root.querySelectorAll(".o_popover, .dropdown-menu, .o-dropdown--menu");
                for (const popover of popovers) {
                    if (popover.querySelector("a.o_app")) {
                        return popover;
                    }
                }
            }
            return null;
        }

        function enrichAppItems(popover) {
            if (!popover || popover.dataset.aivioAppsReady === "1") {
                return;
            }
            const items = [...popover.querySelectorAll("a.o_app")];
            if (!items.length) {
                return;
            }

            popover.classList.add("o_aivio_enterprise_apps_popover");
            popover.dataset.aivioAppsReady = "1";

            const { iconsByID, endMenuIDs } = getAppData();
            const normalItems = [];
            const bottomItems = [];

            for (const item of items) {
                const menuID = String(item.dataset.section || "");
                if (endMenuIDs.has(menuID)) {
                    bottomItems.push(item);
                } else {
                    normalItems.push(item);
                }
            }
            for (const item of normalItems.concat(bottomItems)) {
                popover.appendChild(item);
            }

            for (const item of [...popover.querySelectorAll("a.o_app")]) {
                const menuID = String(item.dataset.section || "");
                const appData = iconsByID[menuID] || {};
                const label = (appData.name || item.textContent || "").trim();

                if (!item.querySelector(".o_aivio_et_app_icon")) {
                    const iconWrap = document.createElement("span");
                    iconWrap.className = "o_aivio_et_app_icon";

                    if (appData.icon) {
                        const img = document.createElement("img");
                        img.src = appData.icon;
                        img.alt = label;
                        iconWrap.appendChild(img);
                    } else {
                        iconWrap.textContent = label ? label[0].toUpperCase() : "?";
                        iconWrap.classList.add("o_aivio_et_app_icon_letter");
                    }

                    item.insertBefore(iconWrap, item.firstChild);
                }

                if (!item.querySelector(".o_aivio_et_app_label")) {
                    const textNodes = [];
                    for (const child of [...item.childNodes]) {
                        if (child.nodeType === Node.TEXT_NODE && child.nodeValue.trim()) {
                            textNodes.push(child);
                        }
                    }
                    for (const node of textNodes) {
                        node.remove();
                    }
                    const labelSpan = document.createElement("span");
                    labelSpan.className = "o_aivio_et_app_label";
                    labelSpan.textContent = label;
                    item.appendChild(labelSpan);
                }
            }
        }

        function scanExistingPopovers() {
            const popovers = document.querySelectorAll(".o_popover, .dropdown-menu, .o-dropdown--menu");
            for (const popover of popovers) {
                if (popover.querySelector("a.o_app")) {
                    enrichAppItems(popover);
                }
            }
        }

        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    const popover = findAppsPopover(node);
                    if (popover) {
                        setTimeout(() => enrichAppItems(popover), 0);
                    }
                }
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });
        setTimeout(scanExistingPopovers, 0);
    },
};

registry.category("services").add("aivio_enterprise_theme.home_menu_icons", aivioHomeMenuIconsService);
