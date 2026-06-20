# AIVIO Enterprise Theme for Odoo 19 Community

Technical module name: `aivio_enterprise_theme`

This build fixes the menu/responsive problems by removing the old DOM-mutation approach and replacing the Odoo Community apps menu through a proper Odoo 19 Owl/QWeb navbar extension.

## What this version changes

- `/odoo` opens the AIVIO Enterprise-style Apps launcher instead of Discuss.
- The Home/Menu button opens a full-screen Enterprise-like app grid.
- The launcher is implemented as an Owl component attached to `web.NavBar.AppsMenu`, not injected after render.
- No mutation of native menu DOM, which avoids broken menus after Odoo rerenders.
- Desktop and mobile use the same stable app launcher.
- App icons are loaded from Odoo menu metadata (`webIcon` / `webIconData`).
- Search, keyboard arrows, Escape close, and active app highlighting are included.
- Responsive fixes for forms, control panel, list horizontal scroll, modals, dropdowns, sticky list headers and footers.
- Removes Odoo promotional branding from login/portal where possible.
- Keeps AIVIO technical copyright: `aivio_enterprise_theme`.

## Important after update

After replacing the module:

1. Restart Odoo.
2. Upgrade `aivio_enterprise_theme` from Apps.
3. Open `/odoo?debug=assets` once.
4. Hard refresh the browser.

If you had one of the older broken builds installed, clear browser cache because the old JS may remain in assets until Odoo rebuilds them.


## 19.0.1.6.0 QWeb hotfix

Removed brittle positional XPath targets from `aivio_apps_menu.xml`. The theme now replaces only the stable desktop `Dropdown` node in `web.NavBar.AppsMenu` and leaves the native Odoo mobile sidebar intact for responsive stability.


## Install safety fix

This build removes brittle login/portal inherited QWeb views and handles debranding through assets so missing XPath targets in different Odoo 19 minor builds cannot block installation.
