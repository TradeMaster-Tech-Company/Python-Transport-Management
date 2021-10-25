# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTmsFactor(TransactionCase):

    def setUp(self):
        super().setUp()
        self.factor = self.env['tms.factor']
        self.employee = self.env.ref('tms.tms_hr_employee_01')

    def test_10_tms_factor_onchange_factor_type(self):
        factor_type_list = [
            ['distance', 'Distance Route (Km/Mi)'],
            ['distance_real', 'Distance Real (Km/Mi)'],
            ['weight', 'Weight'],
            ['travel', 'Travel'],
            ['qty', 'Quantity'],
            ['volume', 'Volume'],
            ['percent', 'Income Percent'],
        ]
        factor = self.factor.create({
            'name': 'distance',
            'category': 'driver',
            'factor_type': 'distance',
        })
        for record in factor_type_list:
            factor.write({'factor_type': record[0]})
            factor._onchange_factor_type()
            self.assertEqual(factor.name, record[1], 'Onchange is not working')

    def create_factor(self):
        return self.factor.create({
            'name': 'distance',
            'category': 'driver',
            'factor_type': 'distance',
            'factor': 2,
        })

    def test_20_get_amount_distance(self):
        factor = self.create_factor()
        value = factor.get_amount(distance=100)
        self.assertEqual(value, 200, 'Error in factor calculation (distance)')

    def test_21_get_amount_distance_range(self):
        factor = self.create_factor()
        factor2 = self.create_factor()
        factor2.factor = 1
        value = factor.get_amount(distance=100)
        self.assertEqual(value, 200, 'Error in factor calculation (distance)')
        value = factor2.get_amount(distance=1500)
        self.assertEqual(value, 1500, 'Error in factor calculation (distance)')

    def test_22_get_amount_distance_fixed_amount(self):
        factor = self.create_factor()
        factor.fixed_amount = 100
        factor.mixed = True
        value = factor.get_amount(distance=100)
        self.assertEqual(value, 300, 'Error in factor calculation (distance)')

    def test_30_get_amount_distance_real(self):
        factor = self.create_factor()
        factor.factor_type = 'distance_real'
        value = factor.get_amount(distance_real=100)
        self.assertEqual(
            value, 200, 'Error in factor calculation (distance_real)')

    def test_31_get_amount_distance_real_range(self):
        factor = self.create_factor()
        factor.factor = 2
        factor.range_start = 0
        factor.factor_type = 'distance_real'
        factor.range_end = 1000
        factor2 = self.create_factor()
        factor2.factor_type = 'distance_real'
        factor2.factor = 1
        factor2.range_start = 1001
        factor2.range_end = 2000
        value = factor.get_amount(distance_real=100)
        self.assertEqual(
            value, 200, 'Error in factor calculation (distance_real)')
        value = factor2.get_amount(distance_real=1500)
        self.assertEqual(
            value, 1500, 'Error in factor calculation (distance_real)')

    def test_32_get_amount_distance_real_fixed_amount(self):
        factor = self.create_factor()
        factor.factor_type = 'distance_real'
        factor.factor = 2
        factor.mixed = True
        factor.fixed_amount = 100
        value = factor.get_amount(distance_real=100)
        self.assertEqual(
            value, 300, 'Error in factor calculation (distance_real)')

    def test_40_get_amount_weight(self):
        factor = self.factor.create({
            'name': 'weight',
            'category': 'driver',
            'factor_type': 'weight',
            'factor': 2,
        })
        value = factor.get_amount(weight=100)
        self.assertEqual(
            value, 200, 'Error in factor calculation (weight)')

    def test_41_get_amount_weight_range(self):
        factor = self.factor.create({
            'name': 'weight',
            'category': 'driver',
            'factor_type': 'weight',
            'range_start': 0,
            'range_end': 1000,
            'factor': 2,
        })
        factor2 = self.factor.create({
            'name': 'weight',
            'category': 'driver',
            'factor_type': 'weight',
            'range_start': 1001,
            'range_end': 2000,
            'factor': 1,
        })
        value = factor.get_amount(weight=100)
        self.assertEqual(
            value, 200, 'Error in factor calculation (weight)')
        value = factor2.get_amount(weight=1500)
        self.assertEqual(
            value, 1500, 'Error in factor calculation (weight)')

    def test_42_get_amount_weight_fixed_amount(self):
        factor = self.factor.create({
            'name': 'weight',
            'category': 'driver',
            'factor_type': 'weight',
            'factor': 2,
            'mixed': True,
            'fixed_amount': 100,
        })
        value = factor.get_amount(weight=100)
        self.assertEqual(
            value, 300, 'Error in factor calculation (weight)')

    def test_50_get_amount_travel(self):
        factor = self.factor.create({
            'name': 'travel',
            'category': 'driver',
            'factor_type': 'travel',
            'fixed_amount': 100,
        })
        value = factor.get_amount()
        self.assertEqual(
            value, 100, 'Error in factor calculation (travel)')

    def test_60_get_amount_qty(self):
        factor = self.factor.create({
            'name': 'qty',
            'category': 'driver',
            'factor_type': 'qty',
            'factor': 2,
        })
        value = factor.get_amount(qty=100)
        self.assertEqual(
            value, 200, 'Error in factor calculation (qty)')

    def test_61_get_amount_qty_range(self):
        factor = self.factor.create({
            'name': 'qty',
            'category': 'driver',
            'factor_type': 'qty',
            'range_start': 0,
            'range_end': 1000,
            'factor': 2,
        })
        factor2 = self.factor.create({
            'name': 'qty',
            'category': 'driver',
            'factor_type': 'qty',
            'range_start': 1001,
            'range_end': 2000,
            'factor': 1,
        })
        value = factor.get_amount(qty=100)
        self.assertEqual(
            value, 200, 'Error in factor calculation (qty)')
        value = factor2.get_amount(qty=1500)
        self.assertEqual(
            value, 1500, 'Error in factor calculation (qty)')

    def test_62_get_amount_qty_fixed_amount(self):
        factor = self.factor.create({
            'name': 'qty',
            'category': 'driver',
            'factor_type': 'qty',
            'factor': 2,
            'mixed': True,
            'fixed_amount': 100,
        })
        value = factor.get_amount(qty=100)
        self.assertEqual(
            value, 300, 'Error in factor calculation (qty)')

    def test_70_get_amount_volume(self):
        factor = self.factor.create({
            'name': 'volume',
            'category': 'driver',
            'factor_type': 'volume',
            'factor': 2,
        })
        value = factor.get_amount(volume=100)
        self.assertEqual(
            value, 200, 'Error in factor calculation (volume)')

    def test_71_get_amount_volume_range(self):
        factor = self.factor.create({
            'name': 'volume',
            'category': 'driver',
            'factor_type': 'volume',
            'range_start': 0,
            'range_end': 1000,
            'factor': 2,
        })
        factor2 = self.factor.create({
            'name': 'volume',
            'category': 'driver',
            'factor_type': 'volume',
            'range_start': 1001,
            'range_end': 2000,
            'factor': 1,
        })
        value = factor.get_amount(volume=100)
        self.assertEqual(
            value, 200, 'Error in factor calculation (volume)')
        value = factor2.get_amount(volume=1500)
        self.assertEqual(
            value, 1500, 'Error in factor calculation (volume)')

    def test_72_get_amount_volume_fixed_amount(self):
        factor = self.factor.create({
            'name': 'volume',
            'category': 'driver',
            'factor_type': 'volume',
            'factor': 2,
            'mixed': True,
            'fixed_amount': 100,
        })
        value = factor.get_amount(volume=100)
        self.assertEqual(
            value, 300, 'Error in factor calculation (volume)')

    def test_80_get_amount_percent(self):
        factor = self.factor.create({
            'name': 'percent',
            'category': 'driver',
            'factor_type': 'percent',
            'factor': 10,
        })
        value = factor.get_amount(income=1000)
        self.assertEqual(
            value, 100, 'Error in factor calculation (percent)')

    def test_81_get_amount_percent_fixed_amount(self):
        factor = self.factor.create({
            'name': 'percent',
            'category': 'driver',
            'factor_type': 'percent',
            'factor': 10,
            'mixed': True,
            'fixed_amount': 100,
        })
        value = factor.get_amount(income=1000)
        self.assertEqual(
            value, 200, 'Error in factor calculation (percent)')

    def test_90_get_driver_amount(self):
        factor = self.create_factor()
        with self.assertRaisesRegex(
                ValidationError,
                'The employee must have a income percentage value'):
            factor.get_driver_amount(self.employee, 500, 100)
        self.employee.income_percentage = 500
        amount = factor.get_driver_amount(self.employee, 500, 100)
        self.assertEqual(amount, 2600, 'Error in amount')
        with self.assertRaisesRegex(
                ValidationError,
                'Invalid parameter you can use this factor only with drivers'):
            factor.get_driver_amount(False, 500, 100)

    def test_100_get_amount(self):
        factor = self.create_factor()
        factor.factor_type = 'percent_driver'
        self.employee.income_percentage = 500
        percent = factor.get_amount(
            employee=self.employee, income=100)
        self.assertEqual(percent, 500.0, 'Error in amount')
        factor.factor_type = 'amount_driver'
        factor.fixed_amount = 100.0
        amount = factor.get_amount(
            employee=self.employee)
        self.assertEqual(amount, 500.0, 'Error in amount')
        with self.assertRaisesRegex(
                ValidationError,
                'the amount isnt between of any ranges'):
            factor.fixed_amount = 0.0
            factor.factor_type = 'distance'
            factor.get_amount(employee=self.employee)
