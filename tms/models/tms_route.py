# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import simplejson as json
from odoo import _, api, exceptions, fields, models


class TmsRoute(models.Model):
    _name = 'tms.route'
    _inherit = 'mail.thread'
    _description = 'Routes'

    name = fields.Char('Route Name', size=64, required=True, index=True)
    departure_id = fields.Many2one('tms.place', 'Departure', required=True)
    arrival_id = fields.Many2one('tms.place', 'Arrival', required=True)
    distance = fields.Float(
        'Distance (mi./kms)', digits=(14, 4),
        help='Route distance (mi./kms)', required=True)
    travel_time = fields.Float(
        'Travel Time (hrs)', digits=(14, 4),
        help='Route travel time (hours)')
    notes = fields.Text()
    active = fields.Boolean(default=True)
    driver_factor_ids = fields.One2many(
        'tms.factor', 'route_id',
        string="Expense driver factor")
    distance_loaded = fields.Float(
        string='Distance Loaded (mi./km)',
        required=True
    )
    distance_empty = fields.Float(
        string='Distance Empty (mi./km)',
        required=True
    )
    fuel_efficiency_ids = fields.One2many(
        'tms.route.fuelefficiency',
        'route_id',
        string="Fuel Efficiency")
    route_place_ids = fields.One2many(
        'tms.route.place',
        'route_id',
        string='Places')
    tollstation_ids = fields.Many2many(
        'tms.route.tollstation', string="Toll Station")
    note_ids = fields.One2many(
        'tms.route.note', 'route_id', string='Notes of Route')

    @api.depends('distance_empty', 'distance')
    @api.onchange('distance_empty')
    def on_change_disance_empty(self):
        for rec in self:
            if rec.distance_empty < 0.0:
                raise exceptions.ValidationError(
                    _("The value must be positive and lower than"
                        " the distance route."))
            rec.distance_loaded = rec.distance - rec.distance_empty

    @api.depends('distance_loaded', 'distance')
    @api.onchange('distance_loaded')
    def on_change_disance_loaded(self):
        for rec in self:
            if rec.distance_loaded < 0.0:
                raise exceptions.ValidationError(
                    _("The value must be positive and lower than"
                        " the distance route."))
            rec.distance_empty = rec.distance - rec.distance_loaded

    def get_route_info(self, error=False):
        for rec in self:
            departure = {
                'latitude': rec.departure_id.latitude,
                'longitude': rec.departure_id.longitude
            }
            arrival = {
                'latitude': rec.arrival_id.latitude,
                'longitude': rec.arrival_id.longitude
            }
            if not departure['latitude'] and not departure['longitude']:
                raise exceptions.UserError(_(
                    "The departure don't have coordinates."))
            if not arrival['latitude'] and not arrival['longitude']:
                raise exceptions.UserError(_(
                    "The arrival don't have coordinates."))
            url = 'http://maps.googleapis.com/maps/api/distancematrix/json'
            origins = (str(departure['latitude']) + ',' +
                       str(departure['longitude']))
            destinations = ''
            places = [str(x.place_id.latitude) + ',' +
                      str(x.place_id.longitude) for x in rec.route_place_ids
                      if x.place_id.latitude and x.place_id.longitude]
            for place in places:
                origins += "|" + place
                destinations += place + "|"
            destinations += (str(arrival['latitude']) + ',' +
                             str(arrival['longitude']))
            params = {
                'origins': origins,
                'destinations': destinations,
                'mode': 'driving',
                'language': self.env.lang,
                'sensor': 'false',
            }
            try:
                result = json.loads(requests.get(url, params=params).content)
                distance = duration = 0.0
                if result['status'] == 'OK':
                    if rec.route_place_ids or (rec.departure_id and
                                               rec.arrival_id):
                        pos = 0
                        for row in result['rows']:
                            distance += (
                                row['elements'][pos]['distance']
                                   ['value'] / 1000.0)
                            duration += (
                                row['elements'][pos]['duration']
                                   ['value'] / 3600.0)
                            pos += 1
                self.distance = distance
                self.travel_time = duration
            except Exception:
                raise exceptions.UserError(_("Google Maps is not available."))

    def open_in_google(self):
        for route in self:
            points = (
                str(route.departure_id.latitude) + ',' +
                str(route.departure_id.longitude) +
                (',' if route.route_place_ids else '') +
                ','.join([str(x.place_id.latitude) + ',' +
                         str(x.place_id.longitude)
                         for x in route.route_place_ids
                         if x.place_id.latitude and x.place_id.longitude]) +
                ',' + str(route.arrival_id.latitude) + ',' +
                str(route.arrival_id.longitude))
            url = "/tms/static/src/googlemaps/get_route.html?" + points
        return {'type': 'ir.actions.act_url',
                'url': url,
                'nodestroy': True,
                'target': 'new'}

    def get_fuel_efficiency(self, vehicle_id, framework):
        for rec in self:
            fuel = self.env['tms.route.fuelefficiency']
            fuel_id = fuel.search([
                ('route_id', '=', rec.id),
                ('engine_id', '=', vehicle_id.engine_id.id),
                ('type', '=', framework)
            ])
        return fuel_id.performance
