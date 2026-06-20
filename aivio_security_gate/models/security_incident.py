# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AivioSecurityIncident(models.Model):
    _name = 'aivio.security.incident'
    _description = 'AIVIO Security Incident'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'incident_datetime desc, id desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    incident_datetime = fields.Datetime(default=fields.Datetime.now, required=True, tracking=True)
    gate_id = fields.Many2one('aivio.security.gate', tracking=True)
    reported_by_id = fields.Many2one('res.users', default=lambda self: self.env.user, tracking=True)
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium', tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='new', tracking=True)
    description = fields.Text(required=True)
    attachment = fields.Binary()
    attachment_filename = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('aivio.security.incident') or _('New')
        return super().create(vals_list)

    def action_done(self):
        self.write({'state': 'done'})
