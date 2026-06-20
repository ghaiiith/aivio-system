# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    aivio_maintenance_team_ids = fields.Many2many(
        'aivio.maintenance.team',
        'aivio_res_users_maintenance_team_rel',
        'user_id', 'team_id',
        string='AIVIO Maintenance Teams',
        help='Maintenance teams this mobile user belongs to or supervises.'
    )
