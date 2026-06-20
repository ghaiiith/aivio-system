# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AivioRealEstateFloor(models.Model):
    _name = 'aivio.real.estate.floor'
    _description = 'Real Estate Floor'
    _order = 'project_id, sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one('aivio.real.estate.project', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    floor_number = fields.Integer()
    area = fields.Float(string='Floor Area')
    image_1920 = fields.Image(string='Floor Plan', max_width=1920, max_height=1920)
    unit_ids = fields.One2many('aivio.real.estate.unit', 'floor_id', string='Units')
    unit_count = fields.Integer(compute='_compute_unit_count')
    note = fields.Text()

    @api.depends('unit_ids')
    def _compute_unit_count(self):
        for floor in self:
            floor.unit_count = len(floor.unit_ids)

    def action_open_units(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Units',
            'res_model': 'aivio.real.estate.unit',
            'view_mode': 'list,kanban,form',
            'domain': [('floor_id', '=', self.id)],
            'context': {'default_project_id': self.project_id.id, 'default_floor_id': self.id},
        }
