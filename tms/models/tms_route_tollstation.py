# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TmsRouteTollstation(models.Model):
    _name = 'tms.route.tollstation'
    _description = 'Tollstation'

    name = fields.Char(required=True)
    place_id = fields.Many2one('tms.place', required=True)
    partner_id = fields.Many2one('res.partner')
    route_ids = fields.Many2many('tms.route')
    credit = fields.Boolean()
    cost_per_axis_ids = fields.One2many(
        'tms.route.tollstation.costperaxis',
        'tollstation_id')
    active = fields.Boolean(default=True)
