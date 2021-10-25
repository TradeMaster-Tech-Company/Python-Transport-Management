# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestTmsWaybillLine(TransactionCase):

    def setUp(self):
        super().setUp()
        self.waybill = self.env['tms.waybill']
        self.operating_unit = self.env.ref(
            'operating_unit.main_operating_unit')
        self.customer = self.env.ref('base.res_partner_2')
        self.departure = self.env.ref('base.res_partner_address_31')
        self.arrival = self.env.ref('base.res_partner_address_3')
        self.freight = self.env.ref('tms.product_freight')
        self.insurance = self.env.ref('tms.product_insurance')

    def create_waybill(self):
        return self.waybill.create({
            'operating_unit_id': self.operating_unit.id,
            'partner_id': self.customer.id,
            'departure_address_id': self.departure.id,
            'arrival_address_id': self.arrival.id,
            'partner_invoice_id': self.customer.id,
            'partner_order_id': self.customer.id,
            'waybill_line_ids': [(0, 0, {
                'product_id': self.freight.id,
                'name': self.freight.name,
            })]
        })

    def test_10_tms_waybill_line_onchange_product_id(self):
        waybill = self.create_waybill()
        waybill.waybill_line_ids.write({
            'product_id': self.insurance.id,
        })
        line = waybill.waybill_line_ids[0]
        line.on_change_product_id()
        self.assertEqual(
            line.name, self.insurance.name)
        self.assertEqual(
            line.account_id, self.insurance.property_account_income_id)
