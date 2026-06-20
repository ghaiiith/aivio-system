# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioFamilyMember(models.Model):
    _name = 'aivio.family.member'
    _description = 'AIVIO Family Member'
    _order = 'resident_id, name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    resident_id = fields.Many2one('aivio.resident.profile', required=True, ondelete='cascade', index=True)
    unit_ids = fields.Many2many(related='resident_id.unit_ids', readonly=True)
    relation = fields.Selection([
        ('spouse', 'Spouse'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('parent', 'Parent'),
        ('relative', 'Relative'),
        ('other', 'Other'),
    ], default='other')
    phone = fields.Char()
    identification_no = fields.Char(string='ID Number')
    birth_date = fields.Date()
    notes = fields.Text()
