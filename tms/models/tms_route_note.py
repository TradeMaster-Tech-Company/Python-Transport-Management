# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TmsRouteNote(models.Model):
    _name = 'tms.route.note'
    _description = 'Notes for route'

    route_id = fields.Many2one('tms.route', string='Route', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner', required=True)
    notes = fields.Html(required=True)
    rules = fields.Html(required=True)
