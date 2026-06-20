# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioBlacklist(models.Model):
    _name = 'aivio.blacklist'
    _description = 'AIVIO Blacklist'
    _order = 'create_date desc'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    visitor_phone = fields.Char(index=True)
    plate_number = fields.Char(index=True)
    reason = fields.Text(required=True)
    date_from = fields.Date(default=fields.Date.context_today)
    date_to = fields.Date()
