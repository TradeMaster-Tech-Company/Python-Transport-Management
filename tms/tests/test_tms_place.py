# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import responses

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTmsPlace(TransactionCase):

    def setUp(self):
        super().setUp()
        self.place = self.env.ref('tms.tms_place_01')
        self.env['ir.config_parameter'].set_param(
            'mapquest.key', 'test')
        self.result = {
            'results': [{
                'locations': [{
                    'latLng': {
                        'lat': 29.4241219,
                        'lng': -98.4936282,
                    },
                }],
            }],
        }

    @responses.activate
    def test_10_tms_place_get_coordinates(self):
        responses.add(
            responses.GET, 'https://www.mapquestapi.com/geocoding/v1/address',
            json={'error': 'not found'}, status=404)
        with self.assertRaisesRegex(
                ValidationError,
                'MapQuest is not available.'):
            self.place.get_coordinates()
        state = self.place.state_id
        self.place.state_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'You need to set a Place and a State Name'):
            self.place.get_coordinates()
        self.place.state_id = state
        self.env['ir.config_parameter'].set_param(
            'mapquest.key', 'key')
        with self.assertRaisesRegex(
                ValidationError,
                'You need to define mapquest.key parameter.'):
            self.place.get_coordinates()

    @responses.activate
    def test_11_tms_place_get_coordinates(self):
        responses.add(
            responses.GET, 'https://www.mapquestapi.com/geocoding/v1/address',
            json=self.result, status=200)
        self.place.get_coordinates()
        self.assertEqual(self.place.latitude, 29.4241219,
                         msg='Latitude is not correct')
        self.assertEqual(self.place.longitude, -98.4936282,
                         msg='Longitude is not correct')

    def test_20_tms_place_open_in_google(self):
        self.place.open_in_google()

    def test_30_tms_place_compute_complete_name(self):
        self.place._compute_complete_name()
        self.assertEqual(self.place.complete_name, 'San Antonio, Texas',
                         'Full Complete Name')

    def test_40_tms_place_compute_complete_name(self):
        self.place.write({'name': 'San Francisco'})
        self.place._compute_complete_name()
        self.assertEqual(
            self.place.complete_name,
            'San Francisco, Texas',
            'On change works')
        self.place.write({'state_id': False})
        self.place._compute_complete_name()
        self.assertEqual(
            self.place.complete_name,
            'San Francisco',
            'On change works')

    def test_50_tms_place_get_country_id(self):
        self.place.get_country_id()
        self.assertEqual(self.place.country_id, self.place.state_id.country_id)
        self.place.state_id = False
        self.place.get_country_id()
        self.assertEqual(self.place.country_id.id, False)
