# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioMaintenanceTicketImage(models.Model):
    _name = 'aivio.maintenance.ticket.image'
    _description = 'AIVIO Maintenance Ticket Image'
    _order = 'create_date desc'

    ticket_id = fields.Many2one('aivio.maintenance.ticket', required=True, ondelete='cascade', index=True)
    name = fields.Char(default='Image')
    image = fields.Image(required=True)
    filename = fields.Char()
    image_type = fields.Selection([
        ('before', 'Before'),
        ('after', 'After'),
        ('other', 'Other'),
    ], default='other')
    note = fields.Char()
