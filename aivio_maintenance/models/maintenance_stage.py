# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioMaintenanceStage(models.Model):
    _name = 'aivio.maintenance.stage'
    _description = 'AIVIO Maintenance Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean()
    is_new = fields.Boolean()
    is_done = fields.Boolean()
    is_cancelled = fields.Boolean()
