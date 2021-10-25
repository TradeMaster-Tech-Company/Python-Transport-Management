# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class FleetVehicleOdometer(models.Model):
    _inherit = ['fleet.vehicle.odometer']

    last_odometer = fields.Float(string='Last Read')
    current_odometer = fields.Float(string='Current Read')
    distance = fields.Float()
    travel_id = fields.Many2one('tms.travel')
