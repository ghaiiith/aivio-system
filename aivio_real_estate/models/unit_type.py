# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioRealEstateUnitType(models.Model):
    _name = 'aivio.real.estate.unit.type'
    _description = 'Real Estate Unit Type'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(default=0)
    description = fields.Text(translate=True)
