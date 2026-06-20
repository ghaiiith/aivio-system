# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioRealEstateAmenity(models.Model):
    _name = 'aivio.real.estate.amenity'
    _description = 'Real Estate Amenity'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(default=0)
    description = fields.Text(translate=True)
