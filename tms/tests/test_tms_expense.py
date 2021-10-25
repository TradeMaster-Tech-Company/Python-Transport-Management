# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestTmsExpense(TransactionCase):

    def setUp(self):
        super().setUp()
        self.tms_expense = self.env['tms.expense']
        self.tms_expense_line = self.env['tms.expense.line']
        self.tms_advance = self.env['tms.advance']
        self.tms_travel = self.env['tms.travel']
        self.tms_log_fuel = self.env['fleet.vehicle.log.fuel']

        # Get initial data
        self.product_fuel = self.env.ref('tms.product_fuel')
        self.product_real_expense = self.env.ref('tms.product_real_expense')
        self.operating_unit = self.env.ref(
            'operating_unit.main_operating_unit')
        self.unit = self.env.ref('tms.tms_fleet_vehicle_05')
        self.driver = self.env.ref('tms.tms_hr_employee_02')
        employee_accont = self.env['account.account'].create({
            "code": 'TestEmployee',
            "name": 'Test Employee',
            "user_type_id": self.env.ref(
                "account.data_account_type_current_assets").id
        })
        self.driver.write({
            'address_home_id': self.env.ref('base.res_partner_2').id,
            'tms_advance_account_id': employee_accont.id,
            'tms_expense_negative_account_id': employee_accont.id})

        self.travel = self.env.ref('tms.tms_travel_05')
        self.travel2 = self.tms_travel.create({
            'operating_unit_id': self.operating_unit.id,
            'unit_id': self.unit.id,
            'employee_id': self.driver.id,
            'route_id': self.env.ref('tms.tms_route_02').id,
        })
        self.travel2.write({
            'fuel_log_ids': [(0, 0, {
                'operating_unit_id': self.operating_unit.id,
                'vendor_id': self.env.ref('base.res_partner_12').id,
                'travel_id': self.travel2.id,
                'vehicle_id': self.unit.id,
                'product_id': self.product_fuel.id,
                'tax_amount': 10.0,
                'price_total': 150.0,
            })],
            'advance_ids': [(0, 0, {
                'operating_unit_id': self.operating_unit.id,
                'travel_id': self.travel2.id,
                'product_id': self.product_real_expense.id,
                'amount': 200.0,
            })],
        })
        self.waybill = self.env['tms.waybill'].create({
            'operating_unit_id': self.operating_unit.id,
            'partner_id': self.env.ref('base.res_partner_2').id,
            'partner_order_id': self.env.ref('base.res_partner_2').id,
            'partner_invoice_id': self.env.ref('base.res_partner_2').id,
            'departure_address_id': self.env.ref('base.res_partner_2').id,
            'arrival_address_id': self.env.ref('base.res_partner_3').id,
            'travel_ids': [(6, 0, [self.travel.id, self.travel2.id])],
            'customer_factor_ids': [(0, 0, {
                'factor_type': 'travel',
                'name': 'Travel',
                'fixed_amount': 1001.5,
                'category': 'customer',
            })],
            'transportable_line_ids': [(0, 0, {
                'transportable_id': self.env.ref(
                    'tms.tms_transportable_01').id,
                'quantity': 100.0,
                'name': 'Sand',
                'transportable_uom_id': self.env.ref('uom.product_uom_ton').id,
            })],
            'driver_factor_ids': [(0, 0, {
                'factor_type': 'travel',
                'name': 'Travel',
                'fixed_amount': 501.5,
                'category': 'driver',
            })],
        })

        # Create advance
        self.tms_advance.create({
            'operating_unit_id': self.operating_unit.id,
            'travel_id': self.travel.id,
            'date': '2018-07-03',
            'product_id': self.product_real_expense.id,
            'amount': 350.00,
        })
        # Confirm fuel vouchers
        self.waybill.travel_ids.mapped('fuel_log_ids').action_approved()
        self.waybill.travel_ids.mapped('fuel_log_ids').action_confirm()
        # Confirm and paid advances.
        self.bank_account = self.env['account.journal'].create({
            'bank_acc_number': '121212',
            'name': 'Test Bank',
            'type': 'bank',
            'code': 'TESTBANK',
        })
        self.waybill.travel_ids.mapped('advance_ids').action_approve()
        self.waybill.travel_ids.mapped('advance_ids').action_authorized()
        self.waybill.travel_ids.mapped('advance_ids').action_confirm()
        self.env['tms.wizard.payment'].with_context({
            'active_ids': self.waybill.travel_ids.mapped(
                'advance_ids').mapped('id'),
            'active_model': 'tms.advance',
        }).create({
            'amount_total': sum(self.travel.advance_ids.mapped('amount')),
            'date': '2018-09-03',
            'journal_id': self.bank_account.id,
        }).make_payment()

        # Confirm travel
        for travel in self.waybill.travel_ids:
            travel.action_progress()
            travel.action_done()

        self.tax = self.env.user.company_id.account_sale_tax_id

    def create_expense(self):
        product_other_income = self.env.ref('tms.product_other_income')
        product_salary_discount = self.env.ref('tms.product_discount')
        product_salary_retention = self.env.ref('tms.product_retention')
        product_made_up_expense = self.env.ref('tms.product_madeup')
        expense = self.tms_expense.create({
            'operating_unit_id': self.operating_unit.id,
            'unit_id': self.unit.id,
            'employee_id': self.driver.id,
            'travel_ids': [(6, 0, [self.travel.id, self.travel2.id])],
            'expense_line_ids': [
                (0, 0, {
                    'travel_id': self.travel.id,
                    'product_id': self.product_fuel.id,
                    'line_type': self.product_fuel.tms_product_category,
                    'name': self.product_fuel.name,
                    'unit_price': 100.0,
                    'partner_id': self.env.ref('base.res_partner_12').id,
                    'invoice_number': '10010101',
                    'date': '2018-08-03',
                }), (0, 0, {
                    'product_id': product_other_income.id,
                    'name': product_other_income.name,
                    'unit_price': 100.0,
                }), (0, 0, {
                    'product_id': product_salary_discount.id,
                    'name': product_salary_discount.name,
                    'unit_price': 100.0,
                }), (0, 0, {
                    'product_id': product_salary_retention.id,
                    'name': product_salary_retention.name,
                    'unit_price': 100.0,
                }), (0, 0, {
                    'product_id': product_made_up_expense.id,
                    'name': product_made_up_expense.name,
                    'unit_price': 100.0,
                }), (0, 0, {
                    'travel_id': self.travel.id,
                    'product_id': self.product_real_expense.id,
                    'line_type': (
                        self.product_real_expense.tms_product_category),
                    'name': self.product_real_expense.name,
                    'unit_price': 900.0,
                    'tax_ids': [(4, self.tax.id)],
                })],
        })
        expense.get_travel_info()
        return expense

    def test_10_tms_expense_create_advance_line(self):
        adv = self.tms_advance.create({
            'operating_unit_id': self.operating_unit.id,
            'travel_id': self.travel.id,
            'unit_id': self.unit.id,
            'employee_id': self.driver.id,
            'product_id': self.product_real_expense.id,
            'amount': 10.0,
        })
        with self.assertRaises(ValidationError) as err:
            self.create_expense()
        self.waybill.travel_ids.mapped('advance_ids').filtered(
            lambda x: x.state == 'closed').write({'state': 'confirmed'})
        self.assertEqual(
            err.exception.args[0],
            'Oops! All the advances must be confirmed or cancelled \n '
            'Name of advance not confirmed or cancelled: ' + adv.name +
            '\n State: ' + adv.state)
        adv.action_approve()
        adv.action_authorized()
        adv.action_confirm()
        with self.assertRaises(ValidationError) as err2:
            self.create_expense()
        self.assertEqual(
            err2.exception.args[0],
            'Oops! All the advances must be paid\n '
            'Name of advance not paid: ' + adv.name)

    def test_20_tms_expense_create_fuel_line(self):
        log = self.tms_log_fuel.create({
            'operating_unit_id': self.operating_unit.id,
            'vendor_id': self.env.ref('base.res_partner_1').id,
            'travel_id': self.travel.id,
            'vehicle_id': self.unit.id,
            'product_id': self.product_fuel.id,
            'tax_amount': 10.0,
            'price_total': 100.0,
        })
        with self.assertRaises(ValidationError) as err:
            self.create_expense()
        self.assertEqual(
            err.exception.args[0],
            'Oops! All the voucher must be confirmed\n '
            'Name of voucher not confirmed: ' + log.name + '\n '
            'State: ' + log.state)

    def test_30_tms_expense_create(self):
        travel_ids = self.tms_travel.search([
            ('employee_id', '=', self.driver.id),
            ('unit_id', '=', self.unit.id),
            ('state', '=', 'done'),
        ]).mapped('id')
        self.assertTrue(self.travel.id in travel_ids)

        expense = self.create_expense()
        self.assertEqual(
            len(expense.expense_line_ids.filtered(
                lambda x: x.line_type == 'salary')),
            len(expense.travel_ids))

        # Salary
        amount_salary = len(self.waybill.travel_ids) * sum(
            self.waybill.driver_factor_ids.mapped('fixed_amount'))
        self.assertEqual(amount_salary, expense.amount_salary)
        # Other Income
        amount_other_income = sum(expense.expense_line_ids.filtered(
            lambda x: x.line_type == 'other_income').mapped('price_total'))
        self.assertEqual(amount_other_income, expense.amount_other_income)
        # Salary Discount
        amount_salary_discount = sum(expense.expense_line_ids.filtered(
            lambda x: x.line_type == 'salary_discount').mapped('price_total'))
        self.assertEqual(
            amount_salary_discount, expense.amount_salary_discount)
        # Salary Retention
        amount_salary_retention = sum(expense.expense_line_ids.filtered(
            lambda x: x.line_type == 'salary_retention').mapped('price_total'))
        self.assertEqual(
            amount_salary_retention, expense.amount_salary_retention)
        # Expenses
        amount_real_expense = sum(expense.expense_line_ids.filtered(
            lambda x: x.line_type == 'real_expense').mapped('price_subtotal'))
        self.assertEqual(amount_real_expense, expense.amount_real_expense)
        # Subtotal (Real)
        amount_subtotal_real = (
            amount_salary +
            amount_salary_discount +
            amount_real_expense +
            amount_salary_retention +
            amount_other_income)
        self.assertEqual(amount_subtotal_real, expense.amount_subtotal_real)
        # Taxes (Real)
        amount_tax_real = sum(expense.expense_line_ids.filtered(
            lambda x: x.line_type == 'real_expense').mapped('tax_amount'))
        self.assertEqual(amount_tax_real, expense.amount_tax_real)
        # Total (Real)
        amount_total_real = amount_subtotal_real + amount_tax_real
        self.assertEqual(amount_total_real, expense.amount_total_real)
        # Advances
        amount_advance = sum(self.waybill.travel_ids.mapped(
            'advance_ids').filtered(lambda x: x.payment_move_id).mapped(
            'amount'))
        self.assertEqual(amount_advance, expense.amount_advance)
        # Balance
        amount_balance = amount_total_real - amount_advance
        self.assertEqual(amount_balance, expense.amount_balance)
        # Cosf of Fuel
        amount_fuel = sum([
            log.price_subtotal + log.special_tax_amount
            for log in expense.fuel_log_ids])
        self.assertEqual(amount_fuel, expense.amount_fuel)
        # SubTotal (All)
        amount_subtotal_total = sum([
            log.price_subtotal + log.special_tax_amount
            for log in expense.travel_ids.mapped('fuel_log_ids')])
        amount_subtotal_total += sum(expense.expense_line_ids.filtered(
            lambda x: x.line_type == 'real_expense').mapped('price_subtotal'))
        amount_subtotal_total += amount_balance
        self.assertEqual(amount_subtotal_total, expense.amount_subtotal_total)
        # Taxes (All)
        amount_tax_total = sum(expense.travel_ids.mapped(
            'fuel_log_ids').mapped('tax_amount')) + amount_tax_real
        self.assertEqual(amount_tax_total, expense.amount_tax_total)
        # Made up expense
        amount_made_up_expense = sum(expense.expense_line_ids.filtered(
            lambda x: x.line_type == 'made_up_expense').mapped('price_total'))
        # Total (All)
        amount_total_total = (
            amount_subtotal_total + amount_tax_total + amount_made_up_expense)
        self.assertEqual(amount_total_total, expense.amount_total_total)

    def test_40_tms_expense_action_confirm(self):
        expense = self.create_expense()
        # Confirm expense.
        expense.action_approved()
        expense.action_confirm()

        fuel_line_ids = expense.fuel_log_ids.filtered(
            lambda x: x.created_from_expense).mapped('expense_line_id')
        line_ids = expense.expense_line_ids.filtered(
            lambda x: x.expense_fuel_log).mapped('id')
        for lid in line_ids:
            self.assertTrue(lid in fuel_line_ids.mapped('id'))

    def test_50_tms_expense_action_cancel(self):
        expense = self.create_expense()
        # Confirm expense.
        expense.action_approved()
        expense.action_confirm()
        # Then cancel expense
        expense.action_cancel()

        if expense.expense_line_ids.filtered(
                lambda x: x.expense_fuel_log):
            self.assertFalse(any(expense.fuel_log_ids.filtered(
                lambda x: x.created_from_expense)))
