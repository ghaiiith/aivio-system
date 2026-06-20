# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AivioRealEstateContract(models.Model):
    _name = 'aivio.real.estate.contract'
    _description = 'Real Estate Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    reservation_id = fields.Many2one('aivio.real.estate.reservation', ondelete='set null', tracking=True)
    partner_id = fields.Many2one('res.partner', required=True, tracking=True, ondelete='restrict')
    unit_id = fields.Many2one('aivio.real.estate.unit', required=True, tracking=True, ondelete='restrict')
    project_id = fields.Many2one(related='unit_id.project_id', store=True, readonly=True)
    region_id = fields.Many2one(related='unit_id.region_id', store=True, readonly=True)
    company_id = fields.Many2one(related='unit_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='unit_id.currency_id', readonly=True)
    contract_type = fields.Selection([
        ('sale', 'Ownership'),
        ('rent', 'Rental'),
    ], default='sale', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True)
    date_start = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    date_end = fields.Date(tracking=True)
    contract_value = fields.Monetary(currency_field='currency_id', required=True, tracking=True)
    deposit_amount = fields.Monetary(currency_field='currency_id')
    installment_count = fields.Integer(default=1)
    payment_frequency = fields.Selection([
        ('once', 'Once'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], default='monthly', required=True)
    first_due_date = fields.Date(default=fields.Date.context_today)
    installment_ids = fields.One2many('aivio.real.estate.installment', 'contract_id', string='Installments')
    installment_total = fields.Monetary(compute='_compute_amounts', currency_field='currency_id')
    amount_invoiced = fields.Monetary(compute='_compute_amounts', currency_field='currency_id')
    amount_paid = fields.Monetary(compute='_compute_amounts', currency_field='currency_id')
    amount_residual = fields.Monetary(compute='_compute_amounts', currency_field='currency_id')
    invoice_count = fields.Integer(compute='_compute_amounts')
    note = fields.Html()

    @api.constrains('contract_value', 'deposit_amount', 'installment_count')
    def _check_contract_values(self):
        for contract in self:
            if contract.contract_value <= 0:
                raise ValidationError(_('Contract value must be greater than zero.'))
            if contract.deposit_amount < 0:
                raise ValidationError(_('Deposit amount cannot be negative.'))
            if contract.deposit_amount > contract.contract_value:
                raise ValidationError(_('Deposit cannot be greater than the contract value.'))
            if contract.installment_count <= 0:
                raise ValidationError(_('Installment count must be greater than zero.'))

    @api.depends('installment_ids.amount', 'installment_ids.invoice_id.amount_total', 'installment_ids.invoice_id.amount_residual', 'installment_ids.invoice_id.state')
    def _compute_amounts(self):
        for contract in self:
            posted_invoices = contract.installment_ids.invoice_id.filtered(lambda m: m.state == 'posted')
            contract.installment_total = sum(contract.installment_ids.mapped('amount'))
            contract.amount_invoiced = sum(posted_invoices.mapped('amount_total'))
            contract.amount_residual = sum(posted_invoices.mapped('amount_residual'))
            contract.amount_paid = contract.amount_invoiced - contract.amount_residual
            contract.invoice_count = len(contract.installment_ids.invoice_id)

    @api.onchange('reservation_id')
    def _onchange_reservation_id(self):
        for contract in self:
            reservation = contract.reservation_id
            if reservation:
                contract.partner_id = reservation.partner_id
                contract.unit_id = reservation.unit_id
                contract.contract_type = reservation.expected_contract_type
                contract.contract_value = reservation.price
                contract.deposit_amount = reservation.deposit_amount

    @api.onchange('unit_id', 'contract_type')
    def _onchange_unit_price(self):
        for contract in self:
            if not contract.contract_value and contract.unit_id:
                contract.contract_value = contract.unit_id.rent_price if contract.contract_type == 'rent' else contract.unit_id.sale_price

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('aivio.real.estate.contract') or _('New')
        return super().create(vals_list)

    def _frequency_delta(self):
        self.ensure_one()
        if self.payment_frequency == 'quarterly':
            return relativedelta(months=3)
        if self.payment_frequency == 'yearly':
            return relativedelta(years=1)
        if self.payment_frequency == 'once':
            return relativedelta(days=0)
        return relativedelta(months=1)

    def action_generate_installments(self):
        Installment = self.env['aivio.real.estate.installment']
        for contract in self:
            if contract.state != 'draft':
                raise UserError(_('Installments can only be regenerated while the contract is in Draft.'))
            old_lines = contract.installment_ids.filtered(lambda line: not line.invoice_id)
            old_lines.unlink()
            amount = round((contract.contract_value - contract.deposit_amount) / contract.installment_count, 2)
            remaining = contract.contract_value - contract.deposit_amount
            due_date = contract.first_due_date or contract.date_start or fields.Date.context_today(contract)
            delta = contract._frequency_delta()
            for number in range(1, contract.installment_count + 1):
                line_amount = amount if number < contract.installment_count else remaining
                Installment.create({
                    'contract_id': contract.id,
                    'sequence': number,
                    'name': _('Installment %s') % number,
                    'due_date': due_date,
                    'amount': line_amount,
                })
                remaining -= line_amount
                due_date = due_date + delta

    def action_confirm(self):
        for contract in self:
            if not contract.installment_ids:
                contract.action_generate_installments()
            if contract.unit_id.state not in ('available', 'reserved', 'maintenance'):
                raise UserError(_('Unit %s is not available for this contract.') % contract.unit_id.display_name)
            contract.state = 'confirmed'
            contract.unit_id.state = 'rented' if contract.contract_type == 'rent' else 'sold'
            contract.message_post(body=_('Contract confirmed. Unit status was updated.'))

    def action_close(self):
        for contract in self:
            contract.state = 'closed'
            if contract.contract_type == 'rent' and contract.unit_id.state == 'rented':
                contract.unit_id.state = 'available'

    def action_cancel(self):
        for contract in self:
            if contract.installment_ids.invoice_id.filtered(lambda move: move.state == 'posted'):
                raise UserError(_('You cannot cancel a contract with posted invoices. Please reverse invoices first.'))
            contract.state = 'cancelled'
            if contract.unit_id.state in ('reserved', 'rented'):
                contract.unit_id.state = 'available'

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_open_invoices(self):
        self.ensure_one()
        invoices = self.installment_ids.invoice_id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'default_move_type': 'out_invoice'},
        }
