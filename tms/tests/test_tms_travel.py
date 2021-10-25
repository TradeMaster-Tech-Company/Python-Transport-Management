# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools.float_utils import float_compare


class TestTmsTravel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.travel_id = self.env.ref("tms.tms_travel_01")
        self.kit = self.env.ref('tms.tms_unit_kit_01')
        self.unit = self.env.ref('tms.tms_fleet_vehicle_01')
        self.dolly_id = self.env.ref('tms.tms_fleet_vehicle_04')
        self.trailer1_id = self.env.ref('tms.tms_fleet_vehicle_02')
        self.trailer2_id = self.env.ref('tms.tms_fleet_vehicle_03')
        self.employee_id = self.env.ref('tms.tms_hr_employee_01')
        self.route = self.env.ref('tms.tms_route_01')
        self.travel_id2 = self.env.ref('tms.tms_travel_02')
        self.advance = self.env.ref('tms.tms_advance_01')
        self.fuel = self.env.ref('tms.tms_fuel_log_01')
        self.operating_unit_id = self.env.ref(
            "operating_unit.main_operating_unit")
        self.customer = self.env.ref('base.res_partner_2')
        self.departure = self.env.ref('base.res_partner_address_31')
        self.arrival = self.env.ref('base.res_partner_address_3')
        self.waybill = self.env['tms.waybill'].create({
            'operating_unit_id': self.operating_unit_id.id,
            'partner_id': self.customer.id,
            'departure_address_id': self.departure.id,
            'arrival_address_id': self.arrival.id,
            'travel_ids': [(4, self.travel_id.id)],
            'partner_invoice_id': self.customer.id,
            'partner_order_id': self.customer.id,
        })

    def test_10_tms_travel_compute_travel_duration(self):
        self.travel_id.date_start = datetime.now()
        date = datetime.now() + timedelta(days=10)
        self.travel_id.date_end = date
        self.travel_id._compute_travel_duration()
        self.assertEqual(float_compare(self.travel_id.travel_duration,
                                       240, precision_digits=2), 0)

    def test_20_tms_travel_compute_travel_duration_real(self):
        self.travel_id.date_start_real = datetime.now()
        date = datetime.now() + timedelta(days=10)
        self.travel_id.date_end_real = date
        self.travel_id._compute_travel_duration_real()
        self.assertEqual(float_compare(self.travel_id.travel_duration_real,
                                       240, precision_digits=2), 0)

    def test_30_tms_travel_onchange_kit(self):
        self.travel_id.kit_id = self.kit.id
        self.travel_id._onchange_kit()
        self.assertEqual(self.travel_id.unit_id, self.unit)
        self.assertEqual(self.travel_id.trailer1_id, self.trailer1_id)
        self.assertEqual(self.travel_id.trailer2_id, self.trailer2_id)
        self.assertEqual(self.travel_id.dolly_id, self.dolly_id)
        self.assertEqual(self.travel_id.employee_id, self.employee_id)

    def test_40_tms_travel_onchange_route(self):
        self.travel_id.route_id = self.route.id
        self.travel_id._onchange_route()
        self.assertEqual(self.travel_id.distance_route, 887.00)
        self.assertEqual(self.travel_id.distance_loaded, 587.00)
        self.assertEqual(self.travel_id.distance_empty, 300.00)
        self.assertEqual(self.travel_id.travel_duration, 07.43)

    def test_50_tms_travel_action_draft(self):
        self.travel_id.state = 'cancel'
        self.travel_id.action_draft()
        self.assertEqual(self.travel_id.state, 'draft')

    def test_60_tms_travel_action_progress(self):
        self.travel_id2.state = 'progress'
        with self.assertRaisesRegex(
                ValidationError, 'The unit or driver are already in use!'):
            self.travel_id.action_progress()

    def test_70_tms_travel_action_cancel(self):
        with self.assertRaisesRegex(
                ValidationError,
                'If you want to cancel this travel,'
                ' you must cancel the fuel logs or the advances '
                'attached to this travel'):
            self.travel_id.action_cancel()
        for advance in self.travel_id.advance_ids:
            advance.state = 'cancel'
        for fuel in self.travel_id.fuel_log_ids:
            fuel.state = 'cancel'
        self.travel_id.action_cancel()
        self.assertEqual(self.travel_id.state, 'cancel')

    def test_80_tms_travel_create(self):
        self.operating_unit_id.travel_sequence_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'You need to define the sequence for travels in base'):
            self.env['tms.travel'].create({
                'state': 'draft',
                'route_id': self.env.ref('tms.tms_route_02').id,
                'unit_id': self.env.ref('tms.tms_fleet_vehicle_01').id,
                'employee_id': self.env.ref('tms.tms_hr_employee_01').id,
                'date': datetime.now(),
                'date_start': datetime.now() + timedelta(days=2),
                'date_end': datetime.now() + timedelta(days=5),
                'operating_unit_id': self.operating_unit_id.id,
            })

    def test_90_tms_travel_copy(self):
        travel_copy = self.travel_id.copy()
        self.assertFalse(travel_copy.waybill_ids, 'You have waybills')

    def test_100_tms_travel_compute_framework(self):
        self.travel_id._compute_framework()
        self.assertEqual(self.travel_id.framework, 'unit')
        self.travel_id.trailer1_id = self.trailer1_id.id
        self.travel_id._compute_framework()
        self.assertEqual(self.travel_id.framework, 'single')
        self.travel_id.trailer2_id = self.travel_id2.id
        self.travel_id._compute_framework()
        self.assertEqual(self.travel_id.framework, 'double')

    def test_110_tms_travel_validate_driver_license(self):
        self.travel_id.employee_id.days_to_expire = 0
        with self.assertRaisesRegex(
                ValidationError,
                "You can not Dispatch this Travel because Fernando Bedoya "
                "Driver s License Validity %s is expired or about "
                "to expire in next 5 days" %
                self.travel_id.employee_id.license_expiration):
            self.travel_id.validate_driver_license()

    def test_120_tms_travel_validate_vehicle_insurance(self):
        self.travel_id.unit_id.insurance_expiration = datetime.now().date()
        with self.assertRaisesRegex(
                ValidationError,
                'You can not Dispatch this Travel because this Vehicle %s '
                'Insurance %s is expired or about to expire in '
                'next 5 days' % (
                    self.travel_id.unit_id.name, self.travel_id.unit_id.insurance_expiration.strftime(  # noqa
                        '%Y-%m-%d'))):
            self.travel_id.validate_vehicle_insurance()
