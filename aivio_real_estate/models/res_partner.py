# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_real_estate_customer = fields.Boolean(string='Real Estate Customer')
    real_estate_reservation_ids = fields.One2many('aivio.real.estate.reservation', 'partner_id', string='Real Estate Reservations')
    real_estate_contract_ids = fields.One2many('aivio.real.estate.contract', 'partner_id', string='Real Estate Contracts')
    real_estate_reservation_count = fields.Integer(compute='_compute_real_estate_counts')
    real_estate_contract_count = fields.Integer(compute='_compute_real_estate_counts')

    def _compute_real_estate_counts(self):
        for partner in self:
            partner.real_estate_reservation_count = len(partner.real_estate_reservation_ids)
            partner.real_estate_contract_count = len(partner.real_estate_contract_ids)

    def action_open_real_estate_reservations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Real Estate Reservations'),
            'res_model': 'aivio.real.estate.reservation',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_open_real_estate_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Real Estate Contracts'),
            'res_model': 'aivio.real.estate.contract',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
