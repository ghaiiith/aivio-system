# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    aivio_unit_ids = fields.Many2many(
        'aivio.real.estate.unit',
        'aivio_res_users_unit_rel',
        'user_id', 'unit_id',
        string='AIVIO Units',
        help='Units/apartments this mobile portal user can access.'
    )
    aivio_resident_profile_ids = fields.One2many('aivio.resident.profile', 'user_id', string='Resident Profiles')
