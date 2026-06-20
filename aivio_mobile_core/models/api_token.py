# -*- coding: utf-8 -*-
import secrets
from datetime import timedelta

from odoo import api, fields, models, _


class AivioApiToken(models.Model):
    _name = 'aivio.api.token'
    _description = 'AIVIO API Token'
    _order = 'create_date desc'

    name = fields.Char(default='API Token', required=True)
    user_id = fields.Many2one('res.users', required=True, ondelete='cascade', index=True)
    token = fields.Char(required=True, copy=False, index=True)
    refresh_token = fields.Char(copy=False, index=True)
    active = fields.Boolean(default=True)
    expires_at = fields.Datetime(index=True)
    last_used_at = fields.Datetime()
    ip_address = fields.Char()
    user_agent = fields.Char()
    device_token = fields.Char()
    app_role = fields.Selection(related='user_id.aivio_app_role', store=False, readonly=True)

    _sql_constraints = [
        ('token_unique', 'unique(token)', 'API token must be unique.'),
        ('refresh_token_unique', 'unique(refresh_token)', 'Refresh token must be unique.'),
    ]

    @api.model
    def _generate_token(self):
        return secrets.token_urlsafe(48)

    @api.model
    def create_for_user(self, user, ttl_days=30, ip_address=None, user_agent=None, device_token=None):
        now = fields.Datetime.now()
        vals = {
            'name': _('Mobile Token - %s') % user.name,
            'user_id': user.id,
            'token': self._generate_token(),
            'refresh_token': self._generate_token(),
            'expires_at': now + timedelta(days=ttl_days),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'device_token': device_token,
        }
        return self.sudo().create(vals)

    def is_valid(self):
        self.ensure_one()
        return bool(self.active and (not self.expires_at or self.expires_at > fields.Datetime.now()))

    def mark_used(self):
        self.sudo().write({'last_used_at': fields.Datetime.now()})

    def revoke(self):
        self.sudo().write({'active': False})

    @api.model
    def cron_cleanup_expired_tokens(self):
        expired = self.sudo().search([
            ('active', '=', True),
            ('expires_at', '!=', False),
            ('expires_at', '<', fields.Datetime.now()),
        ])
        expired.write({'active': False})
