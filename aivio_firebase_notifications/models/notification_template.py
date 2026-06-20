# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioNotificationTemplate(models.Model):
    _name = 'aivio.notification.template'
    _description = 'AIVIO Notification Template'
    _order = 'name'

    name = fields.Char(required=True)
    notification_type = fields.Selection([
        ('general', 'General'),
        ('invoice', 'Invoice'),
        ('maintenance', 'Maintenance'),
        ('visitor', 'Visitor'),
        ('security', 'Security'),
        ('emergency', 'Emergency'),
    ], default='general', required=True)
    title = fields.Char(required=True, translate=True)
    body = fields.Text(required=True, translate=True)
    active = fields.Boolean(default=True)
