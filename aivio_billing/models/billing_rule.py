# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AivioBillingRule(models.Model):
    _name = 'aivio.billing.rule'
    _description = 'AIVIO Billing Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one('product.product', required=True, tracking=True)
    income_account_id = fields.Many2one('account.account', string='Income Account')
    amount = fields.Monetary(required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    billing_type = fields.Selection([
        ('fixed', 'Fixed Monthly'),
        ('area', 'By Unit Area'),
        ('service', 'Service Fee'),
        ('penalty', 'Penalty'),
    ], default='fixed', required=True, tracking=True)
    project_id = fields.Many2one('aivio.real.estate.project', string='Building / Project')
    unit_ids = fields.Many2many('aivio.real.estate.unit', string='Specific Units')
    invoice_day = fields.Integer(default=1)
    last_generated_date = fields.Date(readonly=True)

    def _get_units(self):
        self.ensure_one()
        if self.unit_ids:
            return self.unit_ids
        domain = []
        if self.project_id:
            domain.append(('project_id', '=', self.project_id.id))
        return self.env['aivio.real.estate.unit'].search(domain)

    def _get_resident_for_unit(self, unit):
        return self.env['aivio.resident.profile'].search([
            ('state', '=', 'active'),
            '|', ('primary_unit_id', '=', unit.id), ('unit_ids', 'in', unit.id),
        ], limit=1)

    def action_generate_invoices(self):
        Move = self.env['account.move']
        today = fields.Date.context_today(self)
        created = Move
        for rule in self:
            for unit in rule._get_units():
                resident = rule._get_resident_for_unit(unit)
                if not resident or not resident.partner_id:
                    continue
                amount = rule.amount
                if rule.billing_type == 'area':
                    amount = rule.amount * (unit.area or 1.0)
                account_id = rule.income_account_id.id or rule.product_id.property_account_income_id.id or rule.product_id.categ_id.property_account_income_categ_id.id
                if not account_id:
                    raise UserError(_('Please configure an income account on the billing product or rule.'))
                move = Move.create({
                    'move_type': 'out_invoice',
                    'partner_id': resident.partner_id.id,
                    'invoice_date': today,
                    'aivio_unit_id': unit.id,
                    'aivio_resident_profile_id': resident.id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': rule.product_id.id,
                        'name': rule.name,
                        'quantity': 1.0,
                        'price_unit': amount,
                        'account_id': account_id,
                    })],
                })
                created |= move
            rule.last_generated_date = today
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created.ids)],
        }
