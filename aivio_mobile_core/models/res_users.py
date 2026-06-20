# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    aivio_app_role = fields.Selection([
        ('resident', 'Resident'),
        ('security', 'Security'),
        ('maintenance', 'Maintenance Technician'),
        ('maintenance_supervisor', 'Maintenance Supervisor'),
        ('manager', 'AIVIO Manager'),
    ], string='AIVIO App Role', compute='_compute_aivio_app_role', store=False, readonly=True)
    aivio_api_token_ids = fields.One2many('aivio.api.token', 'user_id', string='AIVIO API Tokens')

    def _compute_aivio_app_role(self):
        for user in self:
            role = False
            if user.has_group('aivio_mobile_core.group_aivio_manager'):
                role = 'manager'
            elif user.has_group('aivio_mobile_core.group_aivio_security_user'):
                role = 'security'
            elif user.has_group('aivio_mobile_core.group_aivio_maintenance_supervisor'):
                role = 'maintenance_supervisor'
            elif user.has_group('aivio_mobile_core.group_aivio_maintenance_user'):
                role = 'maintenance'
            elif user.has_group('aivio_mobile_core.group_aivio_resident_user'):
                role = 'resident'
            user.aivio_app_role = role

    def aivio_get_allowed_apps(self):
        self.ensure_one()
        mapping = {
            'resident': ['resident'],
            'security': ['security'],
            'maintenance': ['maintenance'],
            'maintenance_supervisor': ['maintenance'],
            'manager': ['resident', 'security', 'maintenance', 'admin'],
        }
        return mapping.get(self.aivio_app_role, [])
