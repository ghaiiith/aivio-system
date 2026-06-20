# -*- coding: utf-8 -*-
{
    'name': 'AIVIO Mobile API Gateway',
    'version': '19.0.1.0.0',
    'category': 'AIVIO',
    'summary': 'REST API gateway for Resident, Security, Maintenance apps with OpenAPI and Postman docs.',
    'description': 'Custom mobile REST API for AIVIO on Odoo 19 Community. Includes auth tokens, role checks, resident/security/maintenance/billing/notification endpoints, OpenAPI, Swagger JSON, and Postman collection.',
    'author': 'AIVIO',
    'maintainer': 'AIVIO',
    'website': 'https://www.aivio.ai',
    'license': 'LGPL-3',
    'depends': [
        'aivio_mobile_core',
        'aivio_residence',
        'aivio_security_gate',
        'aivio_maintenance',
        'aivio_billing',
        'aivio_firebase_notifications',
    ],
    'data': [
        'views/api_docs_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
