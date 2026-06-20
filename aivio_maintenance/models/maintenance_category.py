# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioMaintenanceCategory(models.Model):
    _name = 'aivio.maintenance.category'
    _description = 'AIVIO Maintenance Category'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    paid_service = fields.Boolean(string='Paid Service')
    product_id = fields.Many2one('product.product', string='Billing Product')
