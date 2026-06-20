/** @odoo-module **/
// Copyright (C) 2026 aivio_enterprise_theme
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import { Component, useRef, useState, onMounted, useEffect, useExternalListener } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useBus } from "@web/core/utils/hooks";
import { NavBar } from "@web/webclient/navbar/navbar";
import { WebClient } from "@web/webclient/webclient";

const OPEN_BODY_CLASS = "o_aivio_apps_menu_opened";
const OPEN_EVENT = "AIVIO:APPS_MENU:OPEN";
const CLOSE_EVENT = "AIVIO:APPS_MENU:CLOSE";
const STATE_EVENT = "AIVIO:APPS_MENU:STATE_CHANGED";

function getWebIconData(menu) {
    if (!menu) {
        return "/aivio_enterprise_theme/static/description/icon.png";
    }
    if (menu.webIcon) {
        const path = menu.webIcon.replace(",", "/");
        return path.startsWith("/") ? path : `/${path}`;
    }
    const iconData = menu.webIconData || "";
    if (iconData.startsWith("data:image")) {
        return iconData;
    }
    if (iconData) {
        const prefix = iconData.startsWith("P") ? "data:image/svg+xml;base64," : "data:image/png;base64,";
        return prefix + iconData.replace(/\s/g, "");
    }
    return "/aivio_enterprise_theme/static/description/icon.png";
}

patch(WebClient.prototype, {
    setup() {
        super.setup();
        useBus(this.env.bus, STATE_EVENT, ({ detail: open }) => {
            document.body.classList.toggle(OPEN_BODY_CLASS, Boolean(open));
        });
    },

    /**
     * Odoo Community opens the first available app when /odoo has no explicit action.
     * In many databases that is Discuss. Enterprise opens the app launcher. This patch
     * keeps the web client on /odoo and opens the AIVIO app launcher instead.
     */
    _loadDefaultApp() {
        this.env.bus.trigger(OPEN_EVENT);
        this.env.bus.trigger(STATE_EVENT, true);
        try {
            this.title.setParts({ action: "Apps" });
        } catch (_error) {
            // Title service changed upstream. Do not block the web client.
        }
        return Promise.resolve(true);
    },
});

export class AivioAppMenuItem extends Component {
    static template = "aivio_enterprise_theme.AppMenuItem";
    static props = {
        app: Object,
        href: String,
        active: { type: Boolean, optional: true },
        onSelected: Function,
    };

    get iconSrc() {
        return getWebIconData(this.props.app);
    }

    get label() {
        return this.props.app.name || "App";
    }

    onClick(ev) {
        ev.preventDefault();
        this.props.onSelected(this.props.app);
    }
}

export class AivioAppsMenu extends Component {
    static template = "aivio_enterprise_theme.AppsMenu";
    static components = { AivioAppMenuItem };
    static props = {
        apps: { type: Array, optional: true },
        currentApp: { type: Object, optional: true },
        getMenuItemHref: Function,
        onAppSelected: Function,
        isScopedApp: { type: Boolean, optional: true },
    };

    setup() {
        this.state = useState({ open: false, query: "" });
        this.searchInput = useRef("searchInput");

        useBus(this.env.bus, OPEN_EVENT, () => this.open());
        useBus(this.env.bus, CLOSE_EVENT, () => this.close());
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.close());
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this.close());

        useExternalListener(window, "keydown", (ev) => this.onWindowKeydown(ev));
        useExternalListener(window, "resize", () => {
            if (this.state.open) {
                this.focusSearch();
            }
        });

        onMounted(() => {
            if (!this.props.currentApp && !this.props.isScopedApp) {
                // This covers the first render on /odoo before the WebClient patch emits.
                this.open();
            }
        });

        useEffect(
            () => {
                this.env.bus.trigger(STATE_EVENT, this.state.open);
                if (this.state.open) {
                    this.focusSearch();
                }
            },
            () => [this.state.open]
        );
    }

    get apps() {
        const apps = this.props.apps || [];
        const query = this.state.query.trim().toLowerCase();
        if (!query) {
            return apps;
        }
        return apps.filter((app) => (app.name || "").toLowerCase().includes(query));
    }

    get hasNoResults() {
        return Boolean(this.state.query.trim()) && !this.apps.length;
    }

    get columnsCount() {
        if (window.matchMedia("(max-width: 575.98px)").matches) {
            return 3;
        }
        if (window.matchMedia("(max-width: 991.98px)").matches) {
            return 4;
        }
        return 6;
    }

    getItemHref(app) {
        return this.props.getMenuItemHref(app);
    }

    isActive(app) {
        return Boolean(this.props.currentApp && this.props.currentApp.id === app.id);
    }

    open() {
        if (this.props.isScopedApp) {
            return;
        }
        this.state.open = true;
    }

    close() {
        this.state.open = false;
        this.state.query = "";
    }

    toggle() {
        this.state.open ? this.close() : this.open();
    }

    focusSearch() {
        setTimeout(() => this.searchInput.el?.focus({ preventScroll: true }), 30);
    }

    selectApp(app) {
        this.close();
        this.props.onAppSelected(app);
    }

    onSearchInput(ev) {
        this.state.query = ev.target.value || "";
    }

    onOverlayClick(ev) {
        if (ev.target.classList.contains("o_aivio_apps_menu_overlay")) {
            this.close();
        }
    }

    onWindowKeydown(ev) {
        if (!this.state.open) {
            return;
        }
        if (ev.key === "Escape") {
            ev.preventDefault();
            this.close();
            return;
        }
        if (!ev.key.startsWith("Arrow")) {
            return;
        }
        const items = [...document.querySelectorAll(".o_aivio_apps_menu_panel .o_aivio_app_menu_item")];
        if (!items.length) {
            return;
        }
        const current = items.indexOf(document.activeElement);
        let next = current < 0 ? 0 : current;
        if (ev.key === "ArrowRight") {
            next = Math.min(items.length - 1, next + 1);
        } else if (ev.key === "ArrowLeft") {
            next = Math.max(0, next - 1);
        } else if (ev.key === "ArrowDown") {
            next = Math.min(items.length - 1, next + this.columnsCount);
        } else if (ev.key === "ArrowUp") {
            next = Math.max(0, next - this.columnsCount);
        }
        ev.preventDefault();
        items[next]?.focus();
    }
}

patch(NavBar.prototype, {
    openAivioAppsMenu() {
        this.env.bus.trigger(OPEN_EVENT);
    },
});

Object.assign(NavBar.components, { AivioAppsMenu, AivioAppMenuItem });
