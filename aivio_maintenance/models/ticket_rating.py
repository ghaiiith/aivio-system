# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioTicketRating(models.Model):
    _name = 'aivio.ticket.rating'
    _description = 'AIVIO Ticket Rating'
    _order = 'create_date desc'

    ticket_id = fields.Many2one('aivio.maintenance.ticket', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    rating = fields.Integer(required=True)
    feedback = fields.Text()
