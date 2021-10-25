# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo import fields


class TestTmsAdvance(TransactionCase):

    def setUp(self):
        super().setUp()
        self.advance = self.env['tms.advance']
        self.operating_unit = self.env.ref(
            'operating_unit.main_operating_unit')
        self.employee_id = self.env.ref('tms.tms_hr_employee_01')
        self.travel_id1 = self.env.ref("tms.tms_travel_01")
        self.travel_id2 = self.env.ref('tms.tms_travel_02')
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
        self.group = self.env.ref('account.group_account_manager')

    def create_advance(self, amount):
        return self.advance.create({
            "operating_unit_id": self.operating_unit.id,
            "travel_id": self.travel_id1.id,
            "date": fields.Datetime.now(),
            "product_id": self.env.ref("tms.product_real_expense").id,
            "amount": amount,
            "employee_id": self.employee_id.id
        })

    def test_10_tms_advance_create(self):
        with self.assertRaisesRegex(
                ValidationError,
                'The amount must be greater than zero.'):
            self.create_advance(0.0)
        self.operating_unit.advance_sequence_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'The sequence is not defined in operating unit Mexico'):
            self.create_advance(2500.0)

    def test_20_tms_advance_onchange_travel_id(self):
        advance = self.create_advance(2500.0)
        advance.travel_id = self.travel_id2.id
        advance._onchange_travel_id()
        self.assertEqual(advance.unit_id, self.travel_id2.unit_id)
        self.assertEqual(advance.employee_id, self.travel_id2.employee_id)

    def test_30_tms_advance_action_authorized(self):
        advance = self.create_advance(2500.0)
        advance.action_authorized()
        self.assertEqual(advance.state, 'approved')

    def test_40_tms_advance_action_approve(self):
        advance = self.create_advance(2500.0)
        advance.action_approve()
        self.assertEqual(advance.state, 'authorized')
        self.operating_unit.credit_limit = 3000.0
        advance.action_approve()
        self.assertEqual(advance.state, 'approved')

    def create_avance_confirm(self):
        advance = self.create_advance(2500.00)
        self.operating_unit.credit_limit = 3000.0
        advance.action_approve()
        return advance

    def test_50_tms_advance_action_confirm(self):
        advance = self.create_avance_confirm()
        advance.amount = 0.0
        with self.assertRaisesRegex(
                ValidationError,
                'The amount must be greater than zero.'):
            advance.action_confirm()

    def test_51_tms_advance_action_confirm(self):
        advance = self.create_avance_confirm()
        advance.operating_unit_id.advance_journal_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'Warning! The advance does not have a journal'
                ' assigned. Check if you already set the '
                'journal for advances in the base.'):
            advance.action_confirm()

    def test_52_tms_advance_action_confirm(self):
        advance = self.create_avance_confirm()
        advance.employee_id.tms_advance_account_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'Warning! You must have configured the accounts '
                'of the tms'):
            advance.action_confirm()

    def test_53_tms_advance_action_confirm(self):
        advance = self.create_avance_confirm()
        advance.employee_id.address_home_id.property_account_payable_id = False
        with self.assertRaisesRegex(
                ValidationError,
                'Warning! The driver does not have a home address'
                ' assigned. Check if you already set the '
                'home address for the employee.'):
            advance.action_confirm()

    def create_advance_cancel(self):
        advance = self.create_advance(2500.0)
        self.operating_unit.credit_limit = 3000.0
        advance.action_approve()
        advance.action_confirm()
        wizard = self.env['tms.wizard.payment'].with_context({
            'active_model': 'tms.advance',
            'active_ids': [advance.id]}).create({
                'journal_id': self.journal_id.id,
                'amount_total': advance.amount,
            })
        wizard.make_payment()
        return advance

    def cancel_advance(self, advance):
        advance.payment_move_id.line_ids.remove_move_reconcile()
        advance.payment_move_id.button_cancel()
        advance.action_cancel()
        return advance

    def test_60_tms_advance_action_cancel(self):
        advance = self.create_advance_cancel()
        cancel_advance = self.cancel_advance(advance)
        self.assertEqual(cancel_advance.state, 'cancel')

    def test_61_tms_advance_action_cancel(self):
        advance = self.create_advance_cancel()
        self.group.users = False
        with self.assertRaisesRegex(
                ValidationError,
                'Could not cancel this advance because'
                ' the advance is already paid. '
                'Please cancel the payment first.'):
            advance.action_cancel()

    def test_70_tms_advance_action_cancel_draft(self):
        advance = self.create_advance_cancel()
        cancel_advance = self.cancel_advance(advance)
        cancel_advance.travel_id.update({'state': 'cancel'})
        with self.assertRaisesRegex(
                ValidationError,
                'Could not set this advance to draft because'
                ' the travel is cancelled.'):
            advance.action_cancel_draft()

    def test_71_tms_advance_action_cancel_draft(self):
        advance = self.create_advance_cancel()
        cancel_advance = self.cancel_advance(advance)
        cancel_advance.action_cancel_draft()
        self.assertEqual(cancel_advance.state, 'draft')
