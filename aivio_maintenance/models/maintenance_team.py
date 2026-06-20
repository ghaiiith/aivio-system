# -*- coding: utf-8 -*-
from odoo import fields, models


class AivioMaintenanceTeam(models.Model):
    _name = 'aivio.maintenance.team'
    _description = 'AIVIO Maintenance Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    supervisor_user_ids = fields.Many2many('res.users', 'aivio_team_supervisor_rel', 'team_id', 'user_id', string='Supervisors')
    member_user_ids = fields.Many2many('res.users', 'aivio_team_member_rel', 'team_id', 'user_id', string='Technicians')
    default_stage_id = fields.Many2one('aivio.maintenance.stage', string='Default Stage')
    description = fields.Text()
