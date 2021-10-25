# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TmsEvent(models.Model):
    _name = 'tms.event'
    _inherit = 'mail.thread'
    _description = 'Events'
    _order = 'date'

    name = fields.Char(
        string='Description', required=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirm'),
         ('cancel', 'Cancel')], tracking=True, readonly=True, default='draft')
    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
        states={'confirmed': [('readonly', True)],
                'cancel': [('readonly', True)]})
    notes = fields.Text(
        states={'confirmed': [('readonly', True)],
                'cancel': [('readonly', True)]})
    travel_id = fields.Many2one(
        'tms.travel', 'Travel', index=True, required=True, readonly=False,
        states={'confirmed': [('readonly', True)],
                'cancel': [('readonly', True)]}, ondelete='restrict')
    latitude = fields.Float(
        states={'confirmed': [('readonly', True)],
                'cancel': [('readonly', True)]})
    longitude = fields.Float(
        states={'confirmed': [('readonly', True)],
                'cancel': [('readonly', True)]})
    position_real = fields.Text(
        help="Position as GPS",
        states={'confirmed': [('readonly', True)],
                'cancel': [('readonly', True)]})
    position_pi = fields.Text(
        string='Position P.I.', help="Position near a Point of Interest",
        states={'confirmed': [('readonly', True)],
                'cancel': [('readonly', True)]})

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def set_2_draft(self):
        for rec in self:
            rec.state = 'draft'
