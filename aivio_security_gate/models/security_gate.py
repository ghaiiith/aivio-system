# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AivioSecurityGate(models.Model):
    _name = 'aivio.security.gate'
    _description = 'AIVIO Security Gate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    building_id = fields.Many2one('aivio.real.estate.project', string='Building / Project', tracking=True, ondelete='restrict')
    guard_user_ids = fields.Many2many('res.users', 'aivio_gate_guard_user_rel', 'gate_id', 'user_id', string='Allowed Guards')
    latitude = fields.Float(digits=(10, 7))
    longitude = fields.Float(digits=(10, 7))
    notes = fields.Text()

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Gate code must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('aivio.security.gate') or _('New')
        return super().create(vals_list)
