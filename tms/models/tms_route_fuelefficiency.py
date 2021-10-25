# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TmsRouteFuelEficciency(models.Model):
    _name = 'tms.route.fuelefficiency'
    _description = 'Fuel Efficiency by Route'

    route_id = fields.Many2one(
        'tms.route')
    engine_id = fields.Many2one(
        'fleet.vehicle.engine', required=True)
    type = fields.Selection([
        ('unit', 'Unit'),
        ('single', 'Single'),
        ('double', 'Double')
    ], required=True)
    performance = fields.Float(required=True)
