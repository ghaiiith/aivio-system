# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    aivio_gate_ids = fields.Many2many(
        'aivio.security.gate',
        'aivio_res_users_gate_rel',
        'user_id', 'gate_id',
        string='AIVIO Security Gates',
        help='Gates this security mobile user can operate.'
    )
