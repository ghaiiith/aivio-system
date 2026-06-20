# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AivioRealEstateReservation(models.Model):
    _name = 'aivio.real.estate.reservation'
    _description = 'Real Estate Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reservation_date desc, id desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    partner_id = fields.Many2one('res.partner', required=True, tracking=True, ondelete='restrict')
    unit_id = fields.Many2one('aivio.real.estate.unit', required=True, tracking=True, ondelete='restrict')
    project_id = fields.Many2one(related='unit_id.project_id', store=True, readonly=True)
    region_id = fields.Many2one(related='unit_id.region_id', store=True, readonly=True)
    company_id = fields.Many2one(related='unit_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='unit_id.currency_id', readonly=True)
    reservation_date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    expiry_date = fields.Date(default=lambda self: self._default_expiry_date(), tracking=True)
    expected_contract_type = fields.Selection([
        ('sale', 'Ownership'),
        ('rent', 'Rental'),
    ], default='sale', required=True, tracking=True)
    price = fields.Monetary(currency_field='currency_id', compute='_compute_price', readonly=False, store=True)
    deposit_amount = fields.Monetary(currency_field='currency_id', tracking=True)
    note = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('contracted', 'Contracted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True)
    contract_ids = fields.One2many('aivio.real.estate.contract', 'reservation_id', string='Contracts')
    contract_count = fields.Integer(compute='_compute_contract_count')

    @api.model
    def _default_expiry_date(self):
        days = int(self.env['ir.config_parameter'].sudo().get_param('aivio_real_estate.default_reservation_days', 14))
        return fields.Date.context_today(self) + relativedelta(days=days)

    @api.depends('unit_id', 'expected_contract_type')
    def _compute_price(self):
        for reservation in self:
            if reservation.expected_contract_type == 'rent':
                reservation.price = reservation.unit_id.rent_price
            else:
                reservation.price = reservation.unit_id.sale_price

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for reservation in self:
            reservation.contract_count = len(reservation.contract_ids)

    @api.constrains('deposit_amount', 'price')
    def _check_amounts(self):
        for reservation in self:
            if reservation.deposit_amount < 0:
                raise ValidationError(_('Deposit amount cannot be negative.'))
            if reservation.price < 0:
                raise ValidationError(_('Reservation price cannot be negative.'))
            if reservation.price and reservation.deposit_amount > reservation.price:
                raise ValidationError(_('Deposit amount cannot be greater than the reservation price.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('aivio.real.estate.reservation') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        for reservation in self:
            if reservation.unit_id.state not in ('available', 'maintenance'):
                raise UserError(_('Unit %s is not available for reservation.') % reservation.unit_id.display_name)
            reservation.unit_id.state = 'reserved'
            reservation.state = 'confirmed'
            reservation.message_post(body=_('Reservation confirmed and the unit was marked as reserved.'))

    def action_cancel(self):
        for reservation in self:
            reservation.state = 'cancelled'
            if reservation.unit_id.state == 'reserved' and not reservation.contract_ids.filtered(lambda c: c.state not in ('cancelled',)):
                reservation.unit_id.state = 'available'

    def action_mark_expired(self):
        for reservation in self:
            reservation.state = 'expired'
            if reservation.unit_id.state == 'reserved' and not reservation.contract_ids.filtered(lambda c: c.state not in ('cancelled',)):
                reservation.unit_id.state = 'available'

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_create_contract(self):
        self.ensure_one()
        if self.state not in ('confirmed', 'contracted'):
            raise UserError(_('Please confirm the reservation before creating a contract.'))
        contract = self.env['aivio.real.estate.contract'].create({
            'reservation_id': self.id,
            'partner_id': self.partner_id.id,
            'unit_id': self.unit_id.id,
            'contract_type': self.expected_contract_type,
            'contract_value': self.price,
            'deposit_amount': self.deposit_amount,
            'date_start': fields.Date.context_today(self),
        })
        self.state = 'contracted'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract'),
            'res_model': 'aivio.real.estate.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contracts'),
            'res_model': 'aivio.real.estate.contract',
            'view_mode': 'list,form',
            'domain': [('reservation_id', '=', self.id)],
            'context': {'default_reservation_id': self.id},
        }
