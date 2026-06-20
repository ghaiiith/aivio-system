# -*- coding: utf-8 -*-
import secrets
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AivioVisitorVisit(models.Model):
    _name = 'aivio.visitor.visit'
    _description = 'AIVIO Visitor Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_datetime desc, id desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    visitor_name = fields.Char(required=True, tracking=True)
    visitor_phone = fields.Char(index=True, tracking=True)
    visitor_id_number = fields.Char(string='Visitor ID Number')
    visitor_count = fields.Integer(default=1)
    visit_type = fields.Selection([
        ('one_time', 'One Time'),
        ('recurring', 'Recurring'),
        ('delivery', 'Delivery'),
        ('maintenance', 'Maintenance'),
        ('vip', 'VIP'),
    ], default='one_time', required=True)
    reason = fields.Char()
    resident_id = fields.Many2one('aivio.resident.profile', string='Resident', ondelete='restrict', tracking=True)
    resident_user_id = fields.Many2one('res.users', related='resident_id.user_id', store=True, readonly=True)
    unit_id = fields.Many2one('aivio.real.estate.unit', string='Unit / Apartment', ondelete='restrict', tracking=True)
    building_id = fields.Many2one('aivio.real.estate.project', related='unit_id.project_id', store=True, readonly=True)
    gate_id = fields.Many2one('aivio.security.gate', string='Preferred Gate', tracking=True)
    valid_from = fields.Datetime(required=True, default=fields.Datetime.now)
    valid_to = fields.Datetime(required=True)
    visit_datetime = fields.Datetime(default=fields.Datetime.now, tracking=True)
    has_car = fields.Boolean()
    car_plate = fields.Char(index=True)
    qr_token = fields.Char(copy=False, index=True, readonly=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('arrived', 'Arrived'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('denied', 'Denied'),
    ], default='approved', required=True, tracking=True)
    checked_in_at = fields.Datetime(readonly=True)
    checked_out_at = fields.Datetime(readonly=True)
    confirmed_by_id = fields.Many2one('res.users', string='Confirmed By', readonly=True)
    confirmed_gate_id = fields.Many2one('aivio.security.gate', string='Confirmed Gate', readonly=True)
    access_log_ids = fields.One2many('aivio.access.log', 'visit_id', string='Access Logs')
    note = fields.Text()

    _sql_constraints = [
        ('qr_unique', 'unique(qr_token)', 'QR token must be unique.'),
        ('visitor_count_positive', 'CHECK(visitor_count > 0)', 'Visitor count must be greater than zero.'),
    ]

    @api.constrains('valid_from', 'valid_to')
    def _check_dates(self):
        for rec in self:
            if rec.valid_to and rec.valid_from and rec.valid_to <= rec.valid_from:
                raise ValidationError(_('Valid To must be after Valid From.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('aivio.visitor.visit') or _('New')
            vals.setdefault('qr_token', secrets.token_urlsafe(32))
        return super().create(vals_list)

    def _check_not_blacklisted(self):
        Blacklist = self.env['aivio.blacklist'].sudo()
        for rec in self:
            domain = [('active', '=', True), '|', ('visitor_phone', '=', rec.visitor_phone or '-'), ('plate_number', '=', rec.car_plate or '-')]
            if rec.visitor_phone or rec.car_plate:
                if Blacklist.search_count(domain):
                    raise UserError(_('This visitor or vehicle is blacklisted.'))

    def action_check_in(self, gate=None, guard=None):
        for rec in self:
            if rec.status in ('cancelled', 'expired', 'denied', 'checked_out'):
                raise UserError(_('This visit cannot be checked in.'))
            now = fields.Datetime.now()
            if rec.valid_from and now < rec.valid_from:
                raise UserError(_('This visit is not valid yet.'))
            if rec.valid_to and now > rec.valid_to:
                rec.status = 'expired'
                raise UserError(_('This visit has expired.'))
            rec._check_not_blacklisted()
            vals = {
                'status': 'arrived',
                'checked_in_at': now,
                'confirmed_by_id': guard.id if guard else self.env.user.id,
                'confirmed_gate_id': gate.id if gate else rec.gate_id.id,
            }
            rec.write(vals)
            self.env['aivio.access.log'].sudo().create({
                'visit_id': rec.id,
                'event': 'checkin',
                'gate_id': vals['confirmed_gate_id'],
                'guard_id': vals['confirmed_by_id'],
                'datetime': now,
            })

    def action_check_out(self, gate=None, guard=None):
        for rec in self:
            now = fields.Datetime.now()
            rec.write({'status': 'checked_out', 'checked_out_at': now})
            self.env['aivio.access.log'].sudo().create({
                'visit_id': rec.id,
                'event': 'checkout',
                'gate_id': gate.id if gate else rec.confirmed_gate_id.id,
                'guard_id': guard.id if guard else self.env.user.id,
                'datetime': now,
            })

    def action_cancel(self):
        self.write({'status': 'cancelled'})
