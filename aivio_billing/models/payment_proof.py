# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AivioPaymentProof(models.Model):
    _name = 'aivio.payment.proof'
    _description = 'AIVIO Payment Proof'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc, id desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    invoice_id = fields.Many2one('account.move', required=True, domain=[('move_type', '=', 'out_invoice')], tracking=True, ondelete='restrict')
    partner_id = fields.Many2one('res.partner', related='invoice_id.partner_id', store=True, readonly=True)
    unit_id = fields.Many2one('aivio.real.estate.unit', related='invoice_id.aivio_unit_id', store=True, readonly=True)
    resident_id = fields.Many2one('aivio.resident.profile', related='invoice_id.aivio_resident_profile_id', store=True, readonly=True)
    resident_user_id = fields.Many2one('res.users', related='resident_id.user_id', store=True, readonly=True)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True, readonly=True)
    payment_date = fields.Date(default=fields.Date.context_today, required=True)
    attachment = fields.Binary(required=True)
    attachment_filename = fields.Char()
    note = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='submitted', required=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('aivio.payment.proof') or _('New')
        return super().create(vals_list)

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})
