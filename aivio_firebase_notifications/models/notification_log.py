# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioNotificationLog(models.Model):
    _name = 'aivio.notification.log'
    _description = 'AIVIO Notification Delivery Log'
    _order = 'create_date desc'

    notification_id = fields.Many2one('aivio.notification', required=True, ondelete='cascade')
    token_id = fields.Many2one('aivio.mobile.device.token', ondelete='set null')
    status = fields.Selection([('success', 'Success'), ('failed', 'Failed')], required=True)
    response = fields.Text()
    error_message = fields.Text()
