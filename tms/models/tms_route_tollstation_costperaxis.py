# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TmsRouteTollstationCostperaxis(models.Model):
    _name = 'tms.route.tollstation.costperaxis'
    _description = 'Cost Per Axis'

    axis = fields.Integer(required=True)
    cost_credit = fields.Float(required=True)
    cost_cash = fields.Float(required=True)
    tollstation_id = fields.Many2one(
        'tms.route.tollstation',
        string='Toll Station')
