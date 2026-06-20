# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AivioRealEstateRegion(models.Model):
    _name = 'aivio.real.estate.region'
    _description = 'Real Estate Region'
    _inherit = ['mail.thread']
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    active = fields.Boolean(default=True)
    parent_id = fields.Many2one('aivio.real.estate.region', string='Parent Region', index=True, ondelete='restrict')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('aivio.real.estate.region', 'parent_id', string='Sub Regions')
    complete_name = fields.Char(compute='_compute_complete_name', store=True, recursive=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    project_ids = fields.One2many('aivio.real.estate.project', 'region_id', string='Projects')
    project_count = fields.Integer(compute='_compute_counts')
    unit_count = fields.Integer(compute='_compute_counts')
    note = fields.Text()

    _sql_constraints = [
        ('region_code_company_uniq', 'unique(code, company_id)', 'The region code must be unique per company.'),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for region in self:
            if region.parent_id:
                region.complete_name = '%s / %s' % (region.parent_id.complete_name, region.name)
            else:
                region.complete_name = region.name or ''

    def _compute_counts(self):
        Project = self.env['aivio.real.estate.project']
        Unit = self.env['aivio.real.estate.unit']
        for region in self:
            region.project_count = Project.search_count([('region_id', 'child_of', region.id)])
            region.unit_count = Unit.search_count([('region_id', 'child_of', region.id)])

    def action_open_projects(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Projects',
            'res_model': 'aivio.real.estate.project',
            'view_mode': 'list,kanban,form',
            'domain': [('region_id', 'child_of', self.id)],
            'context': {'default_region_id': self.id},
        }

    def action_open_units(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Units',
            'res_model': 'aivio.real.estate.unit',
            'view_mode': 'list,kanban,form',
            'domain': [('region_id', 'child_of', self.id)],
            'context': {'default_region_id': self.id},
        }
