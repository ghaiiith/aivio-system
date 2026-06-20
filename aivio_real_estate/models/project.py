# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AivioRealEstateProject(models.Model):
    _name = 'aivio.real.estate.project'
    _description = 'Real Estate Project / Building'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planning', 'Planning'),
        ('available', 'Available'),
        ('closed', 'Closed'),
    ], default='draft', tracking=True, required=True)
    region_id = fields.Many2one('aivio.real.estate.region', required=True, tracking=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    address = fields.Char()
    latitude = fields.Float(digits=(10, 7))
    longitude = fields.Float(digits=(10, 7))
    image_1920 = fields.Image(max_width=1920, max_height=1920)
    description = fields.Html()
    floor_ids = fields.One2many('aivio.real.estate.floor', 'project_id', string='Floors')
    unit_ids = fields.One2many('aivio.real.estate.unit', 'project_id', string='Units')
    floor_count = fields.Integer(compute='_compute_counts')
    unit_count = fields.Integer(compute='_compute_counts')
    available_unit_count = fields.Integer(compute='_compute_counts')
    reserved_unit_count = fields.Integer(compute='_compute_counts')
    sold_unit_count = fields.Integer(compute='_compute_counts')
    rented_unit_count = fields.Integer(compute='_compute_counts')
    occupancy_rate = fields.Float(compute='_compute_counts')

    _sql_constraints = [
        ('project_code_company_uniq', 'unique(code, company_id)', 'The project code must be unique per company.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('aivio.real.estate.project') or _('New')
        return super().create(vals_list)

    def _compute_counts(self):
        Unit = self.env['aivio.real.estate.unit']
        Floor = self.env['aivio.real.estate.floor']
        for project in self:
            project.floor_count = Floor.search_count([('project_id', '=', project.id)])
            units = Unit.search([('project_id', '=', project.id)])
            project.unit_count = len(units)
            project.available_unit_count = len(units.filtered(lambda u: u.state == 'available'))
            project.reserved_unit_count = len(units.filtered(lambda u: u.state == 'reserved'))
            project.sold_unit_count = len(units.filtered(lambda u: u.state == 'sold'))
            project.rented_unit_count = len(units.filtered(lambda u: u.state == 'rented'))
            occupied = project.sold_unit_count + project.rented_unit_count
            project.occupancy_rate = (occupied / project.unit_count * 100.0) if project.unit_count else 0.0

    def action_set_planning(self):
        self.write({'state': 'planning'})

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_open_units(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Units'),
            'res_model': 'aivio.real.estate.unit',
            'view_mode': 'list,kanban,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id, 'default_region_id': self.region_id.id},
        }

    def action_open_floors(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Floors'),
            'res_model': 'aivio.real.estate.floor',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
