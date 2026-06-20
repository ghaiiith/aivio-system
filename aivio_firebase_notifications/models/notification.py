# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioNotification(models.Model):
    _name = 'aivio.notification'
    _description = 'AIVIO Notification'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', ondelete='cascade', index=True)
    title = fields.Char(required=True)
    body = fields.Text(required=True)
    notification_type = fields.Selection([
        ('general', 'General'),
        ('invoice', 'Invoice'),
        ('maintenance', 'Maintenance'),
        ('visitor', 'Visitor'),
        ('security', 'Security'),
        ('emergency', 'Emergency'),
    ], default='general', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ], default='queued', tracking=True)
    related_model = fields.Char()
    related_res_id = fields.Integer()
    data_json = fields.Text()
    sent_date = fields.Datetime()
    read_date = fields.Datetime()

    def action_mark_read(self):
        self.write({'state': 'read', 'read_date': fields.Datetime.now()})

    def action_queue(self):
        self.write({'state': 'queued'})

    def action_sent(self):
        self.write({'state': 'sent', 'sent_date': fields.Datetime.now()})
