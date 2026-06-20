# -*- coding: utf-8 -*-
# Copyright (C) 2026 aivio_enterprise_theme
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'AIVIO Enterprise Web Theme',
    'version': '19.0.1.6.2',
    'sequence': 7,
    'summary': 'AIVIO backend theme that makes Odoo Community look and feel closer to Enterprise',
    'description': """
AIVIO Enterprise Web Theme
==========================

Backend theme for Odoo 19 Community. The technical module name is
`aivio_enterprise_theme` and the user interface is styled with an
Enterprise-like experience:

* Full-screen applications launcher with icon grid.
* White Enterprise-style backend navbar.
* App icons injected from Odoo menu metadata.
* Enterprise-like control panel, list, form, button, dropdown, modal, and scrollbar styling.
* AIVIO login screen styling and technical copyright.
* Dark mode and RTL refinements.
* Responsive backend improvements implemented against Odoo 19 web client structure.
* Removes Odoo promotional branding from login, portal sidebar, and brand promotion templates.

This module does not depend on Enterprise-only backend modules. It customizes
Community web UI assets and templates only.
    """,
    'author': 'AIVIO',
    'maintainer': 'AIVIO',
    'company': 'AIVIO',
    'website': 'https://aivio.app',
    'license': 'AGPL-3',
    'category': 'Themes/Backend',
    'depends': [
        'web',
    ],
    # Keep this module install-safe across Odoo 19 minor builds.
    # Login/portal debranding is handled by assets, not brittle inherited views.
    'data': [],
    'assets': {
        'web.assets_backend': [
            ('prepend', '/aivio_enterprise_theme/static/src/scss/primary_variables_custom.scss'),
            '/aivio_enterprise_theme/static/src/scss/secondary_variables.scss',
            '/aivio_enterprise_theme/static/src/scss/fields_extra_custom.scss',
            '/aivio_enterprise_theme/static/src/css/aivio_enterprise_webclient.css',
            '/aivio_enterprise_theme/static/src/js/aivio_apps_menu.js',
            '/aivio_enterprise_theme/static/src/xml/aivio_apps_menu.xml',
        ],
        'web.assets_frontend': [
            '/aivio_enterprise_theme/static/src/css/login_theme.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
}
