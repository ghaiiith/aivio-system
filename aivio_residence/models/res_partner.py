# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Odoo 19 Community builds used by AIVIO may not include a native `mobile` field
    # on res.partner. We define it here so resident profiles can safely reuse it.
    mobile = fields.Char(string='Mobile')

    aivio_resident_profile_ids = fields.One2many('aivio.resident.profile', 'partner_id', string='AIVIO Resident Profiles')
    aivio_resident_profile_count = fields.Integer(compute='_compute_aivio_resident_profile_count')

    def _compute_aivio_resident_profile_count(self):
        for partner in self:
            partner.aivio_resident_profile_count = len(partner.aivio_resident_profile_ids)

    def action_open_aivio_resident_profiles(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'AIVIO Resident Profiles',
            'res_model': 'aivio.resident.profile',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
