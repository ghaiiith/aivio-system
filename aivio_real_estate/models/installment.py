# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AivioRealEstateInstallment(models.Model):
    _name = 'aivio.real.estate.installment'
    _description = 'Real Estate Installment'
    _order = 'due_date, sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    contract_id = fields.Many2one('aivio.real.estate.contract', required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='contract_id.partner_id', store=True, readonly=True)
    unit_id = fields.Many2one(related='contract_id.unit_id', store=True, readonly=True)
    project_id = fields.Many2one(related='contract_id.project_id', store=True, readonly=True)
    company_id = fields.Many2one(related='contract_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='contract_id.currency_id', readonly=True)
    due_date = fields.Date(required=True)
    amount = fields.Monetary(currency_field='currency_id', required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False)
    invoice_state = fields.Selection(related='invoice_id.state', string='Invoice Status', readonly=True)
    payment_state = fields.Selection(related='invoice_id.payment_state', string='Payment Status', readonly=True)
    amount_residual = fields.Monetary(related='invoice_id.amount_residual', currency_field='currency_id', readonly=True)
    note = fields.Text()

    @api.constrains('amount')
    def _check_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(_('Installment amount must be greater than zero.'))

    def _get_income_account(self):
        self.ensure_one()
        params = self.env['ir.config_parameter'].sudo()
        account_id = int(params.get_param('aivio_real_estate.income_account_id') or 0)
        if account_id:
            account = self.env['account.account'].browse(account_id)
            if account.exists():
                return account
        product = self.unit_id.product_id
        account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
        if account:
            return account
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        if journal.default_account_id:
            return journal.default_account_id
        raise UserError(_('Please configure an income account in Real Estate settings or on the linked product category.'))

    def action_create_invoice(self):
        Move = self.env['account.move']
        for line in self:
            if line.invoice_id:
                raise UserError(_('An invoice already exists for installment %s.') % line.display_name)
            if line.contract_id.state != 'confirmed':
                raise UserError(_('Only confirmed contracts can be invoiced.'))
            account = line._get_income_account()
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': line.partner_id.id,
                'invoice_date': fields.Date.context_today(line),
                'invoice_date_due': line.due_date,
                'company_id': line.company_id.id,
                'invoice_origin': line.contract_id.name,
                'invoice_line_ids': [(0, 0, {
                    'name': '%s - %s' % (line.contract_id.name, line.name),
                    'quantity': 1.0,
                    'price_unit': line.amount,
                    'account_id': account.id,
                    'product_id': line.unit_id.product_id.id if line.unit_id.product_id else False,
                })],
            }
            line.invoice_id = Move.create(invoice_vals)
        return self.action_open_invoice()

    def action_open_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_('No invoice has been created for this installment yet.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
