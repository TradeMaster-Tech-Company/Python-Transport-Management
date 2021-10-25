# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: skip-file

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTmsExpenseLoan(TransactionCase):

    def setUp(self):
        super().setUp()
        self.expense_loan = self.env['tms.expense.loan']
        self.operating_unit = self.env.ref(
            'operating_unit.main_operating_unit')
        self.employee_id = self.env.ref('tms.tms_hr_employee_01')
        self.unit = self.env.ref('tms.tms_fleet_vehicle_01')
        self.product = self.env.ref('tms.product_loan')
        address = self.env.ref('base.res_partner_2')
        obj_account = self.env['account.account']
        employee_accont = obj_account.create({
            "code": 'TestEmployee',
            "name": 'Test Employee',
            "user_type_id": self.env.ref(
                "account.data_account_type_current_assets").id
        })
        self.employee_id.write({
            'address_home_id': address.id,
            'tms_advance_account_id': employee_accont.id,
            'tms_expense_negative_account_id': employee_accont.id,
            'tms_loan_account_id': employee_accont.id,
        })
        self.journal_id = self.env['account.journal'].create({
            'name': 'Test Bank',
            'type': 'bank',
            'code': 'TESTBANK',
        })

    def create_expense_loan(self):
        return self.expense_loan.create({
            "operating_unit_id": self.operating_unit.id,
            "employee_id": self.employee_id.id,
            "product_id": self.env.ref('tms.product_loan').id,
            "amount": 100.00,
            "discount_type": "fixed",
            "discount_method": "each"
        })

    def create_expense(self):
        expense = self.env['tms.expense'].create({
            'operating_unit_id': self.operating_unit.id,
            'unit_id': self.unit.id,
            'employee_id': self.employee_id.id,
            'expense_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'line_type': self.product.tms_product_category,
                'unit_price': 10.0, })]
        })
        return expense

    def test_10_tms_expense_loan_create(self):
        self.operating_unit.loan_sequence_id = False
        with self.assertRaisesRegex(
                ValidationError, 'You need to define the sequence for loans '
                'in base Mexico'):
            self.create_expense_loan()

    def test_20_tms_expense_loand_action_authorized(self):
        loan = self.create_expense_loan()
        loan.action_authorized()
        self.assertEqual(loan.state, 'approved')

    def test_30_tms_expense_loan_action_approve(self):
        loan = self.create_expense_loan()
        msg = ('Could not approve the Loan. The Amount of discount must be '
               'greater than zero.')
        with self.assertRaisesRegex(ValidationError, msg):
            loan.action_approve()
        loan.discount_type = 'percent'
        with self.assertRaisesRegex(ValidationError, msg):
            loan.action_approve()

    def test_40_tms_expense_loan_action_cancel(self):
        loan = self.create_expense_loan()
        loan.fixed_discount = 10.0
        loan.action_approve()
        loan.action_confirm()
        wizard = self.env['tms.wizard.payment'].with_context({
            'active_model': 'tms.expense.loan',
            'active_ids': [loan.id]}).create({
                'journal_id': self.journal_id.id,
                'amount_total': loan.amount,
            })
        wizard.make_payment()
        loan.action_cancel()

    def test_50_tms_expense_loan_action_confirm(self):
        loan = self.create_expense_loan()
        loan.operating_unit_id.loan_journal_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'Warning! The loan does not have a journal'
                ' assigned. Check if you already set the '
                'journal for loans in the base.'):
            loan.action_confirm()

    def test_51_tms_expense_loan_action_confirm(self):
        loan = self.create_expense_loan()
        loan.employee_id.address_home_id.property_account_payable_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'Warning! The driver does not have a home address'
                ' assigned. Check if you already set the '
                'home address for the employee.'):
            loan.action_confirm()

    def test_52_tms_expense_loan_action_confirm(self):
        loan = self.create_expense_loan()
        loan.employee_id.tms_loan_account_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'Warning! You must have configured the accounts of the tms'):
            loan.action_confirm()

    def test_60_tms_expense_loan_unlink(self):
        loan = self.create_expense_loan()
        loan.fixed_discount = 10.0
        loan.action_approve()
        loan.action_confirm()
        with self.assertRaisesRegex(
                ValidationError,
                'You can not delete a Loan in status confirmed or closed'):
            loan.unlink()
        loan.action_cancel()
        loan.action_cancel_draft()
        loan.unlink()

    def test_70_tms_expense_loan_compute_balance(self):
        loan = self.create_expense_loan()
        expense = self.create_expense()
        loan.expense_ids = expense.expense_line_ids
        loan._compute_balance()
        self.assertEqual(loan.balance, 90.0)
        loan.expense_ids.update({
            'product_id': self.product.id,
            'unit_price': 100.0,
            'line_type': self.product.tms_product_category,
            'name': self.product.name,
            'price_total': -100.00
        })
        loan._compute_balance()
        self.assertEqual(loan.balance, 0.0)
        self.assertEqual(loan.state, 'closed')
