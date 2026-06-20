# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AivioResidentProfile(models.Model):
    _name = 'aivio.resident.profile'
    _description = 'AIVIO Resident Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True, default=lambda self: _('New'))
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', required=True, tracking=True, ondelete='restrict')
    user_id = fields.Many2one('res.users', string='Mobile Portal User', tracking=True, ondelete='set null')
    resident_type = fields.Selection([
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
        ('family', 'Family Member'),
        ('staff', 'Staff'),
    ], required=True, default='tenant', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('blocked', 'Blocked'),
        ('left', 'Left'),
    ], default='active', required=True, tracking=True)
    unit_ids = fields.Many2many(
        'aivio.real.estate.unit',
        'aivio_resident_unit_rel',
        'resident_id', 'unit_id',
        string='Units / Apartments',
        tracking=True,
    )
    primary_unit_id = fields.Many2one('aivio.real.estate.unit', string='Primary Unit', tracking=True)
    phone = fields.Char(related='partner_id.phone', readonly=False)
    mobile = fields.Char(related='partner_id.mobile', readonly=False)
    email = fields.Char(related='partner_id.email', readonly=False)
    emergency_contact_name = fields.Char()
    emergency_contact_phone = fields.Char()
    family_member_ids = fields.One2many('aivio.family.member', 'resident_id', string='Family Members')
    vehicle_ids = fields.One2many('aivio.resident.vehicle', 'resident_id', string='Vehicles')
    family_member_count = fields.Integer(compute='_compute_counts')
    vehicle_count = fields.Integer(compute='_compute_counts')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and self.name == _('New'):
            self.name = self.partner_id.name

    @api.constrains('primary_unit_id', 'unit_ids')
    def _check_primary_unit(self):
        for rec in self:
            if rec.primary_unit_id and rec.primary_unit_id not in rec.unit_ids:
                raise ValidationError(_('Primary unit must be one of the resident units.'))

    @api.depends('family_member_ids', 'vehicle_ids')
    def _compute_counts(self):
        for rec in self:
            rec.family_member_count = len(rec.family_member_ids)
            rec.vehicle_count = len(rec.vehicle_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New') and vals.get('partner_id'):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                vals['name'] = partner.name
        records = super().create(vals_list)
        records._sync_user_units()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {'user_id', 'unit_ids', 'primary_unit_id'} & set(vals):
            self._sync_user_units()
        return res

    def _sync_user_units(self):
        for rec in self.filtered('user_id'):
            units = rec.unit_ids
            if rec.primary_unit_id:
                units |= rec.primary_unit_id
            existing = rec.user_id.aivio_unit_ids
            rec.user_id.sudo().write({'aivio_unit_ids': [(6, 0, (existing | units).ids)]})

    def action_open_family_members(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Family Members'),
            'res_model': 'aivio.family.member',
            'view_mode': 'list,form',
            'domain': [('resident_id', '=', self.id)],
            'context': {'default_resident_id': self.id},
        }

    def action_open_vehicles(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vehicles'),
            'res_model': 'aivio.resident.vehicle',
            'view_mode': 'list,form',
            'domain': [('resident_id', '=', self.id)],
            'context': {'default_resident_id': self.id},
        }
