# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTmsWaybill(TransactionCase):

    def setUp(self):
        super().setUp()
        self.waybill = self.env['tms.waybill']
        self.operating_unit = self.env.ref(
            'operating_unit.main_operating_unit')
        self.customer = self.env.ref('base.res_partner_2')
        self.customer3 = self.env.ref('base.res_partner_3')
        self.departure = self.env.ref('base.res_partner_address_31')
        self.arrival = self.env.ref('base.res_partner_address_3')
        self.freight = self.env.ref('tms.product_freight')
        self.insurance = self.env.ref('tms.product_insurance')
        self.travel_id1 = self.env.ref("tms.tms_travel_01")
        self.transportable = self.env.ref('tms.tms_transportable_01')
        self.transportable2 = self.env.ref('tms.tms_transportable_02')
        self.tax = self.env.user.company_id.account_sale_tax_id
        self.journal_id = self.env['account.journal'].create({
            'name': 'Test Bank',
            'type': 'bank',
            'code': 'TESTBANK',
        })

    def create_waybill(self):
        return self.waybill.create({
            'operating_unit_id': self.operating_unit.id,
            'partner_id': self.customer.id,
            'departure_address_id': self.departure.id,
            'arrival_address_id': self.arrival.id,
            'travel_ids': [(4, self.travel_id1.id)],
            'partner_invoice_id': self.customer.id,
            'partner_order_id': self.customer.id,
            'transportable_line_ids': [(0, 0, {
                'transportable_id': self.transportable.id,
                'name': self.transportable.name,
                'transportable_uom_id': self.transportable.uom_id.id,
                'quantity': 10
            })],
            'customer_factor_ids': [(0, 0, {
                'factor_type': 'travel',
                'name': 'Travel',
                'fixed_amount': 100.00,
                'category': 'customer',
            })],
        })

    def test_10_tms_waybill_onchange_partner_id(self):
        waybill = self.create_waybill()
        waybill.partner_id = self.customer3.id
        waybill.onchange_partner_id()
        address = self.customer3.address_get(
            ['invoice', 'contact']).get('contact', False)
        self.assertEqual(waybill.partner_order_id.id, address)
        self.assertEqual(waybill.partner_invoice_id.id, address)

    def create_waybill_invoice_paid(self):
        waybill = self.create_waybill()
        waybill.action_approve()
        waybill.action_confirm()
        wizard = self.env['tms.wizard.invoice'].with_context({
            'active_model': 'tms.waybill',
            'active_ids': [waybill.id]}).create({})
        wizard.make_invoices()
        waybill.invoice_id.action_post()
        obj_payment = self.env['account.payment']
        payment = obj_payment.create({
            'partner_type': 'customer',
            'journal_id': self.journal_id.id,
            'partner_id': self.customer.id,
            'amount': waybill.amount_total,
            'payment_type': 'inbound',
            'payment_method_id': 1,
        })
        payment.action_post()
        invoice = json.loads(
            waybill.invoice_id.invoice_outstanding_credits_debits_widget)
        waybill.invoice_id.js_assign_outstanding_line(
            invoice['content'][0]['id'])
        return waybill

    def test_20_tms_waybill_compute_invoice_paid(self):
        waybill = self.create_waybill_invoice_paid()
        waybill.invoice_id.payment_state = "paid"
        waybill._compute_invoice_paid()
        self.assertTrue(waybill.invoice_paid, 'she have invoice paid')

    def test_30_tms_waybill_onchange_waybill_line_ids(self):
        waybill = self.create_waybill()
        waybill._onchange_waybill_line_ids()
        self.assertEqual(waybill.waybill_line_ids.unit_price, 100.0)

    def test_40_tms_waybill_amount(self):
        waybill = self.create_waybill()
        products = [
            ('freight', '_compute_amount_freight', 'amount_freight'),
            ('move', '_compute_amount_move', 'amount_move'),
            ('tolls', '_compute_amount_highway_tolls', 'amount_highway_tolls'),
            ('insurance', '_compute_amount_insurance', 'amount_insurance'),
            ('other', '_compute_amount_other', 'amount_other')
        ]
        for product in products:
            product_id = self.env['product.product'].search([
                ('tms_product_category', '=', product[0])])
            waybill.waybill_line_ids.product_id = product_id.id
            getattr(waybill, product[1])()
            amount = getattr(waybill, product[2])
            self.assertEqual(amount, 100.0)

    def test_50_tms_waybill_action_confirm(self):
        waybill = self.create_waybill()
        waybill.travel_ids = False
        waybill.action_approve()
        with self.assertRaisesRegex(
                ValidationError,
                'Could not confirm Waybill !'
                'Waybill must be assigned to a Travel before '
                'confirming.'):
            waybill.action_confirm()

    def test_60_tms_waybill_onchange_waybill_line_ids(self):
        waybill = self.create_waybill()
        waybill.waybill_line_ids.tax_ids = self.tax
        waybill.onchange_waybill_line_ids()
        self.assertEqual(waybill.tax_line_ids[0].tax_id, self.tax)
        self.assertEqual(waybill.tax_line_ids[0].tax_amount, 16.0)
        waybill.waybill_line_ids.create({
            'product_id': self.insurance.id,
            'name': self.insurance.name,
            'unit_price': 100.0,
            'tax_ids': [(4, self.tax.id)],
            'price_subtotal': 100.0,
            'waybill_id': waybill.id
        })
        waybill.onchange_waybill_line_ids()
        self.assertEqual(waybill.tax_line_ids[0].tax_amount, 32.0)

    def test_70_tms_waybill_action_cancel_draft(self):
        waybill = self.create_waybill()
        waybill.action_approve()
        waybill.action_cancel()
        with self.assertRaisesRegex(
                ValidationError,
                'Could not set to draft this Waybill !'
                'Travel is Cancelled !!!'):
            waybill.travel_ids.state = 'cancel'
            waybill.action_cancel_draft()
        waybill.travel_ids.state = 'draft'
        waybill.action_cancel_draft()

    def test_80_tms_waybill_amount_to_text(self):
        waybill = self.create_waybill()
        mxn = self.env.ref('base.MXN').name
        amount = waybill._amount_to_text(1500.00, mxn)
        self.assertEqual(amount, 'MIL QUINIENTOS PESOS 0/100 M.N.')
        usd = self.env.ref('base.USD').name
        amount = waybill._amount_to_text(1500.00, usd, partner_lang="es_USD")
        self.assertEqual(amount, 'ONE THOUSAND, FIVE HUNDRED USD 0/100 M.E.')

    def test_90_tms_waybill_transportable_product(self):
        waybill = self.create_waybill()
        waybill.transportable_line_ids.transportable_id = (
            self.transportable2.id)
        waybill.transportable_line_ids._onchange_transportable_id()
        waybill.customer_factor_ids.update({
            'factor_type': 'volume',
            'name': 'Volume',
            'fixed_amount': 0.0,
            'category': 'customer',
            'factor': 100,
            'range_start': 1,
            'range_end': 200,
        })
        waybill._compute_transportable_product()
        self.assertEqual(waybill.product_volume, 10)

    def test_100_tms_waybill_action_cancel(self):
        waybill = self.create_waybill()
        waybill.action_confirm()
        wizard = self.env['tms.wizard.invoice'].with_context({
            'active_model': 'tms.waybill',
            'active_ids': [waybill.id]}).create({})
        wizard.make_invoices()
        with self.assertRaisesRegex(
                ValidationError,
                'You cannot unlink the invoice of this waybill'
                ' because the invoice is still valid, '
                'please check it.'):
            waybill.action_cancel()
