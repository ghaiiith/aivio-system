# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_real_estate_unit = fields.Boolean(string='Real Estate Unit Product', copy=False)
    real_estate_unit_ids = fields.One2many('aivio.real.estate.unit', 'product_tmpl_id', string='Real Estate Units')
