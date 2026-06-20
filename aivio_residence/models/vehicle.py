# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AivioResidentVehicle(models.Model):
    _name = 'aivio.resident.vehicle'
    _description = 'AIVIO Resident Vehicle'
    _order = 'plate_number'

    name = fields.Char(compute='_compute_name', store=True)
    active = fields.Boolean(default=True)
    resident_id = fields.Many2one('aivio.resident.profile', required=True, ondelete='cascade', index=True)
    unit_id = fields.Many2one('aivio.real.estate.unit', string='Unit / Apartment')
    plate_number = fields.Char(required=True, index=True)
    vehicle_type = fields.Selection([
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
        ('truck', 'Truck'),
        ('other', 'Other'),
    ], default='car')
    brand = fields.Char()
    model = fields.Char()
    color = fields.Char()
    authorized = fields.Boolean(default=True)
    notes = fields.Text()

    _sql_constraints = [
        ('plate_unique', 'unique(plate_number)', 'Plate number must be unique.'),
    ]

    @api.depends('plate_number')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.plate_number or 'Vehicle'
