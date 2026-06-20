# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioMobileDeviceToken(models.Model):
    _name = 'aivio.mobile.device.token'
    _description = 'AIVIO Mobile Device Token'
    _order = 'last_seen desc, id desc'

    user_id = fields.Many2one('res.users', required=True, ondelete='cascade', index=True)
    token = fields.Char(required=True, index=True)
    platform = fields.Selection([('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')], default='android')
    app_name = fields.Selection([('resident', 'Resident'), ('security', 'Security'), ('maintenance', 'Maintenance')])
    app_role = fields.Selection(related='user_id.aivio_app_role', store=False, readonly=True)
    active = fields.Boolean(default=True)
    last_seen = fields.Datetime(default=fields.Datetime.now)
    device_name = fields.Char()

    _sql_constraints = [
        ('token_unique', 'unique(token)', 'Device token must be unique.'),
    ]
