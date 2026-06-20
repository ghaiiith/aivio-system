# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AivioRealEstateUnit(models.Model):
    _name = 'aivio.real.estate.unit'
    _description = 'Real Estate Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id, floor_id, code, name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='project_id.currency_id', readonly=True)
    project_id = fields.Many2one('aivio.real.estate.project', required=True, tracking=True, ondelete='restrict')
    region_id = fields.Many2one('aivio.real.estate.region', related='project_id.region_id', store=True, readonly=True)
    floor_id = fields.Many2one('aivio.real.estate.floor', domain="[('project_id', '=', project_id)]", ondelete='set null')
    unit_type_id = fields.Many2one('aivio.real.estate.unit.type', string='Unit Type')
    amenity_ids = fields.Many2many('aivio.real.estate.amenity', string='Amenities')
    state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
        ('blocked', 'Blocked'),
        ('maintenance', 'Maintenance'),
    ], default='available', required=True, tracking=True)
    sale_price = fields.Monetary(currency_field='currency_id', tracking=True)
    rent_price = fields.Monetary(currency_field='currency_id', tracking=True)
    area = fields.Float(string='Area')
    bedrooms = fields.Integer()
    bathrooms = fields.Integer()
    parking_slots = fields.Integer()
    furnished = fields.Boolean()
    product_tmpl_id = fields.Many2one('product.template', string='Linked Product', ondelete='set null')
    product_id = fields.Many2one('product.product', compute='_compute_product_id', store=True, readonly=True)
    image_1920 = fields.Image(max_width=1920, max_height=1920)
    description = fields.Html()
    image_ids = fields.One2many('aivio.real.estate.unit.image', 'unit_id', string='Images')
    reservation_ids = fields.One2many('aivio.real.estate.reservation', 'unit_id', string='Reservations')
    contract_ids = fields.One2many('aivio.real.estate.contract', 'unit_id', string='Contracts')
    reservation_count = fields.Integer(compute='_compute_counts')
    contract_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('unit_code_company_uniq', 'unique(code, company_id)', 'The unit code must be unique per company.'),
        ('positive_sale_price', 'CHECK(sale_price >= 0)', 'Sale price must be positive.'),
        ('positive_rent_price', 'CHECK(rent_price >= 0)', 'Rent price must be positive.'),
    ]

    @api.depends('product_tmpl_id.product_variant_id')
    def _compute_product_id(self):
        for unit in self:
            unit.product_id = unit.product_tmpl_id.product_variant_id if unit.product_tmpl_id else False

    @api.depends('reservation_ids', 'contract_ids')
    def _compute_counts(self):
        for unit in self:
            unit.reservation_count = len(unit.reservation_ids)
            unit.contract_count = len(unit.contract_ids)

    @api.constrains('floor_id', 'project_id')
    def _check_floor_project(self):
        for unit in self:
            if unit.floor_id and unit.floor_id.project_id != unit.project_id:
                raise ValidationError(_('The selected floor must belong to the selected project.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('aivio.real.estate.unit') or _('New')
        units = super().create(vals_list)
        units._ensure_product_template()
        return units

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ('name', 'sale_price', 'rent_price')):
            self._sync_product_template_values()
        return res

    def _ensure_product_template(self):
        ProductTemplate = self.env['product.template'].sudo()
        for unit in self.filtered(lambda u: not u.product_tmpl_id):
            tmpl_vals = {
                'name': unit.display_name,
                'sale_ok': True,
                'purchase_ok': False,
                'list_price': unit.sale_price or unit.rent_price or 0.0,
                'is_real_estate_unit': True,
            }
            unit.product_tmpl_id = ProductTemplate.create(tmpl_vals)

    def _sync_product_template_values(self):
        for unit in self.filtered('product_tmpl_id'):
            unit.product_tmpl_id.sudo().write({
                'name': unit.display_name,
                'list_price': unit.sale_price or unit.rent_price or 0.0,
                'is_real_estate_unit': True,
            })

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_block(self):
        self.write({'state': 'blocked'})

    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})

    def action_open_reservations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reservations'),
            'res_model': 'aivio.real.estate.reservation',
            'view_mode': 'list,form',
            'domain': [('unit_id', '=', self.id)],
            'context': {'default_unit_id': self.id, 'default_partner_id': False},
        }

    def action_open_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contracts'),
            'res_model': 'aivio.real.estate.contract',
            'view_mode': 'list,form',
            'domain': [('unit_id', '=', self.id)],
            'context': {'default_unit_id': self.id},
        }

    def action_create_reservation(self):
        self.ensure_one()
        if self.state not in ('available', 'maintenance'):
            raise UserError(_('Only available units can be reserved.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Reservation'),
            'res_model': 'aivio.real.estate.reservation',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_unit_id': self.id, 'default_expected_contract_type': 'sale'},
        }
