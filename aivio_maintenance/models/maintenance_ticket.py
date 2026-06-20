# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AivioMaintenanceTicket(models.Model):
    _name = 'aivio.maintenance.ticket'
    _description = 'AIVIO Maintenance Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    subject = fields.Char(required=True, tracking=True)
    description = fields.Text(required=True)
    resident_id = fields.Many2one('aivio.resident.profile', string='Resident', ondelete='restrict', tracking=True)
    resident_user_id = fields.Many2one('res.users', related='resident_id.user_id', store=True, readonly=True)
    unit_id = fields.Many2one('aivio.real.estate.unit', string='Unit / Apartment', ondelete='restrict', tracking=True)
    category_id = fields.Many2one('aivio.maintenance.category', tracking=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Emergency'),
    ], default='1', tracking=True)
    stage_id = fields.Many2one('aivio.maintenance.stage', tracking=True, group_expand='_read_group_stage_ids')
    team_id = fields.Many2one('aivio.maintenance.team', tracking=True)
    assigned_user_id = fields.Many2one('res.users', string='Technician', tracking=True)
    image_ids = fields.One2many('aivio.maintenance.ticket.image', 'ticket_id', string='Images')
    worksheet_ids = fields.One2many('aivio.maintenance.worksheet', 'ticket_id', string='Worksheets')
    rating_ids = fields.One2many('aivio.ticket.rating', 'ticket_id', string='Ratings')
    state = fields.Selection([
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('waiting', 'Waiting Parts'),
        ('done', 'Done'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], default='new', tracking=True)
    expected_date = fields.Datetime()
    closed_date = fields.Datetime(readonly=True)
    average_rating = fields.Float(compute='_compute_average_rating', store=True)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return self.env['aivio.maintenance.stage'].search([])

    @api.depends('rating_ids.rating')
    def _compute_average_rating(self):
        for ticket in self:
            ratings = ticket.rating_ids.mapped('rating')
            ticket.average_rating = sum(ratings) / len(ratings) if ratings else 0.0

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id and self.team_id.default_stage_id and not self.stage_id:
            self.stage_id = self.team_id.default_stage_id

    @api.constrains('assigned_user_id', 'team_id')
    def _check_assigned_user_team(self):
        for ticket in self:
            if ticket.assigned_user_id and ticket.team_id and ticket.assigned_user_id not in ticket.team_id.member_user_ids:
                raise ValidationError(_('Assigned technician must be a member of the selected maintenance team.'))

    @api.model_create_multi
    def create(self, vals_list):
        Stage = self.env['aivio.maintenance.stage']
        default_stage = Stage.search([('is_new', '=', True)], limit=1) or Stage.search([], limit=1)
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('aivio.maintenance.ticket') or _('New')
            vals.setdefault('stage_id', default_stage.id if default_stage else False)
        return super().create(vals_list)

    def action_assign(self):
        for ticket in self:
            if not ticket.assigned_user_id:
                raise UserError(_('Please select a technician first.'))
            ticket.state = 'assigned'

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_waiting(self):
        self.write({'state': 'waiting'})

    def action_done(self):
        done_stage = self.env['aivio.maintenance.stage'].search([('is_done', '=', True)], limit=1)
        vals = {'state': 'done', 'closed_date': fields.Datetime.now()}
        if done_stage:
            vals['stage_id'] = done_stage.id
        self.write(vals)

    def action_cancel(self):
        cancel_stage = self.env['aivio.maintenance.stage'].search([('is_cancelled', '=', True)], limit=1)
        vals = {'state': 'cancelled'}
        if cancel_stage:
            vals['stage_id'] = cancel_stage.id
        self.write(vals)
