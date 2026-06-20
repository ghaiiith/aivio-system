# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioAdsBanner(models.Model):
    _name = 'aivio.ads.banner'
    _description = 'AIVIO Resident App Banner'
    _order = 'sequence, id desc'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    title = fields.Char(required=True)
    subtitle = fields.Char()
    image_1920 = fields.Image(max_width=1920, max_height=1920)
    link_url = fields.Char()
    target_type = fields.Selection([
        ('all', 'All Residents'),
        ('building', 'Building / Project'),
        ('unit', 'Specific Units'),
    ], default='all', required=True)
    project_id = fields.Many2one('aivio.real.estate.project', string='Building / Project')
    unit_ids = fields.Many2many('aivio.real.estate.unit', string='Units')
    date_from = fields.Date()
    date_to = fields.Date()
