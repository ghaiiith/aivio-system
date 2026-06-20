# Developer Notes — aivio_enterprise_theme

## Technical module name

`aivio_enterprise_theme`

## Main fix in 19.0.1.5.0

The earlier builds used runtime DOM mutation to reshape Odoo's app menu. That can break menu display because Odoo 19 rerenders the navbar, dropdowns, and mobile sidebar through Owl components.

This version removes the mutation layer and implements the launcher with a proper Owl/QWeb extension:

- `static/src/xml/aivio_apps_menu.xml`
  - Extends `web.NavBar.AppsMenu`.
  - Replaces the Community desktop dropdown and mobile menu trigger with `AivioAppsMenu`.

- `static/src/js/aivio_apps_menu.js`
  - Defines `AivioAppsMenu` and `AivioAppMenuItem`.
  - Patches `WebClient._loadDefaultApp()` so `/odoo` opens Apps instead of Discuss.
  - Patches `NavBar.components` to register the AIVIO components.

- `static/src/css/aivio_enterprise_webclient.css`
  - Enterprise-like app launcher styling.
  - Responsive layout fixes for forms, lists, modals, dropdowns, and control panel.
  - Dark mode and RTL rules.

## Safety notes

- No dependency on Enterprise-only modules.
- No copy of Odoo Enterprise proprietary code.
- The web client structure is based on Odoo 19 Community `web.NavBar.AppsMenu` and uses safe extension points.
- The old files `aivio_enterprise_home.js` and `aivio_responsive_features.js` were removed because they caused menu display conflicts.
