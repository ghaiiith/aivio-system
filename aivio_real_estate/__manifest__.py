# -*- coding: utf-8 -*-
{
    'name': 'AIVIO Real Estate Management',
    'version': '19.0.1.0.4',
    'category': 'Real Estate',
    'summary': 'Community-ready real estate projects, units, reservations, contracts, installments, and invoicing.',
    'description': """
AIVIO Real Estate Management
============================

A clean Odoo 19 Community module for managing real estate projects, buildings, units,
reservations, ownership/rental contracts, installment schedules, and customer invoices.

Key Features
------------
* Region and project/building hierarchy.
* Unit catalog with floor plans, unit images, amenities, prices, and availability states.
* Reservation lifecycle with expiry dates and customer deposits.
* Ownership and rental contract lifecycle.
* Installment schedule generation and customer invoice creation.
* Accounting integration using Odoo Community account.move invoices.
* Security groups for users and managers.
* Clean Odoo 19 XML views using list views and inline modifiers.
""",
    'author': 'AIVIO',
    'maintainer': 'AIVIO',
    'website': 'https://www.aivio.ai',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
        'product',
        'account',
    ],
    'data': [
        'security/real_estate_security.xml',
        'security/ir.model.access.csv',
        'data/real_estate_sequences.xml',
        'data/real_estate_data.xml',
        'views/region_views.xml',
        'views/project_views.xml',
        'views/floor_views.xml',
        'views/unit_type_views.xml',
        'views/amenity_views.xml',
        'views/unit_views.xml',
        'views/reservation_views.xml',
        'views/contract_views.xml',
        'views/installment_views.xml',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
        'report/real_estate_contract_report.xml',
        'views/real_estate_menus.xml',
    ],
    'demo': [
        'data/real_estate_demo.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
