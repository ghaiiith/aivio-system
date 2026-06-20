# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    aivio_unit_id = fields.Many2one('aivio.real.estate.unit', string='AIVIO Unit / Apartment', index=True)
    aivio_resident_profile_id = fields.Many2one('aivio.resident.profile', string='AIVIO Resident', index=True)
    aivio_contract_id = fields.Many2one('aivio.real.estate.contract', string='AIVIO Contract')
    aivio_ticket_id = fields.Many2one('aivio.maintenance.ticket', string='AIVIO Maintenance Ticket')
