# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioAccessLog(models.Model):
    _name = 'aivio.access.log'
    _description = 'AIVIO Access Log'
    _order = 'datetime desc, id desc'

    visit_id = fields.Many2one('aivio.visitor.visit', ondelete='cascade', index=True)
    event = fields.Selection([
        ('checkin', 'Check-in'),
        ('checkout', 'Check-out'),
        ('denied', 'Denied'),
        ('manual', 'Manual'),
    ], required=True, index=True)
    gate_id = fields.Many2one('aivio.security.gate', ondelete='set null')
    guard_id = fields.Many2one('res.users', ondelete='set null')
    datetime = fields.Datetime(default=fields.Datetime.now, required=True)
    note = fields.Text()
