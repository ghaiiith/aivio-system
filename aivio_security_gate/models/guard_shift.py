# -*- coding: utf-8 -*-
from odoo import fields, models, _


class AivioGuardShift(models.Model):
    _name = 'aivio.guard.shift'
    _description = 'AIVIO Guard Shift'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, start_datetime desc'

    name = fields.Char(required=True, default=lambda self: _('New'))
    gate_id = fields.Many2one('aivio.security.gate', required=True, ondelete='restrict', tracking=True)
    user_id = fields.Many2one('res.users', string='Guard', required=True, tracking=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    start_datetime = fields.Datetime(required=True)
    end_datetime = fields.Datetime()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    note = fields.Text()

    def action_open(self):
        self.write({'state': 'open'})

    def action_close(self):
        self.write({'state': 'closed', 'end_datetime': fields.Datetime.now()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
