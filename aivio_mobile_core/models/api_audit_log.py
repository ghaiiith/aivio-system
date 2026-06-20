# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioApiAuditLog(models.Model):
    _name = 'aivio.api.audit.log'
    _description = 'AIVIO API Audit Log'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', ondelete='set null', index=True)
    endpoint = fields.Char(required=True, index=True)
    method = fields.Char(index=True)
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
        ('denied', 'Denied'),
    ], default='success', index=True)
    ip_address = fields.Char()
    payload = fields.Text()
    response_message = fields.Char()
