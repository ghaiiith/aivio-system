# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    real_estate_default_reservation_days = fields.Integer(
        string='Default Reservation Validity',
        default=14,
        config_parameter='aivio_real_estate.default_reservation_days',
        help='Default number of days used to calculate reservation expiry dates.',
    )
    real_estate_income_account_id = fields.Many2one(
        'account.account',
        string='Real Estate Income Account',
        config_parameter='aivio_real_estate.income_account_id',
        domain="[('account_type', 'in', ['income', 'income_other'])]",
        help='Fallback income account used when creating real estate installment invoices.',
    )
