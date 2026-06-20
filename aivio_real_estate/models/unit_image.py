# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioRealEstateUnitImage(models.Model):
    _name = 'aivio.real.estate.unit.image'
    _description = 'Real Estate Unit Image'
    _order = 'sequence, id'

    name = fields.Char(required=True, default='Image')
    sequence = fields.Integer(default=10)
    unit_id = fields.Many2one('aivio.real.estate.unit', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='unit_id.company_id', store=True, readonly=True)
    image_1920 = fields.Image(required=True, max_width=1920, max_height=1920)
    description = fields.Char()
    active = fields.Boolean(default=True)
