# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TmsPlace(models.Model):
    _name = 'tms.place'
    _description = 'Cities / Places'

    name = fields.Char('Place', size=64, required=True, index=True)
    complete_name = fields.Char(compute='_compute_complete_name')
    state_id = fields.Many2one(
        'res.country.state',
        string='State Name')
    country_id = fields.Many2one(
        'res.country',
        string='Country')
    latitude = fields.Float(
        required=False, digits=(20, 10),
        help='GPS Latitude')
    longitude = fields.Float(
        required=False, digits=(20, 10),
        help='GPS Longitude')

    @api.onchange('state_id')
    def get_country_id(self):
        for rec in self:
            if rec.state_id:
                rec.country_id = rec.state_id.country_id
            else:
                rec.country_id = False

    def get_coordinates(self):
        for rec in self:
            if rec.name and rec.state_id:
                address = (rec.name + "," + rec.state_id.name + "," +
                           rec.state_id.country_id.name)
            else:
                raise ValidationError(
                    _("You need to set a Place and a State Name"))
            key = self.env['ir.config_parameter'].get_param('mapquest.key')
            if key == 'key':
                raise ValidationError(_(
                    "You need to define mapquest.key parameter."))
            params = {
                'key': key,
                'outFormat': 'json',
                'location': address.encode('utf-8'),
                'thumbMaps': 'false',

            }
            url = 'https://www.mapquestapi.com/geocoding/v1/address'
            result = requests.get(url, params=params)
            if result.status_code == 200:
                data = result.json()
                location = data['results'][0]['locations'][0]['latLng']
                self.latitude = location['lat']
                self.longitude = location['lng']
            else:
                raise ValidationError(_("MapQuest is not available."))

    def open_in_google(self):
        for place in self:
            url = ("/tms/static/src/googlemaps/get_place_from_coords.html?" +
                   str(place.latitude) + ',' + str(place.longitude))
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'nodestroy': True,
            'target': 'new'}

    @api.depends('name', 'state_id')
    def _compute_complete_name(self):
        for rec in self:
            if rec.state_id:
                rec.complete_name = rec.name + ', ' + rec.state_id.name
            else:
                rec.complete_name = rec.name
