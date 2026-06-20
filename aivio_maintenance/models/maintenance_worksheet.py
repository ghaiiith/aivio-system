# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioMaintenanceWorksheet(models.Model):
    _name = 'aivio.maintenance.worksheet'
    _description = 'AIVIO Maintenance Worksheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_date desc, id desc'

    name = fields.Char(default='Worksheet', required=True)
    ticket_id = fields.Many2one('aivio.maintenance.ticket', required=True, ondelete='cascade', tracking=True)
    technician_id = fields.Many2one('res.users', default=lambda self: self.env.user, tracking=True)
    work_date = fields.Datetime(default=fields.Datetime.now)
    start_datetime = fields.Datetime()
    end_datetime = fields.Datetime()
    work_note = fields.Text(required=True)
    materials_note = fields.Text()
    resident_signature = fields.Binary(string='Resident Signature')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ], default='draft', tracking=True)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})
