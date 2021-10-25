# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestTmsWaybillTrasnportableLine(TransactionCase):

    def setUp(self):
        super().setUp()
        self.waybill = self.env['tms.waybill']
        self.operating_unit = self.env.ref(
            'operating_unit.main_operating_unit')
        self.customer = self.env.ref('base.res_partner_2')
        self.departure = self.env.ref('base.res_partner_address_31')
        self.arrival = self.env.ref('base.res_partner_address_3')
        self.sand = self.env.ref('tms.tms_transportable_01')
        self.water = self.env.ref('tms.tms_transportable_02')

    def create_waybill(self):
        return self.waybill.create({
            'operating_unit_id': self.operating_unit.id,
            'partner_id': self.customer.id,
            'departure_address_id': self.departure.id,
            'arrival_address_id': self.arrival.id,
            'partner_invoice_id': self.customer.id,
            'partner_order_id': self.customer.id,
            'transportable_line_ids': [(0, 0, {
                'transportable_id': self.sand.id,
                'name': self.sand.name,
                'transportable_uom_id': self.sand.uom_id.id,
            })]
        })

    def test_10_product_template_unique_product_per_category(self):
        waybill = self.create_waybill()
        waybill.transportable_line_ids.write({
            'transportable_id': self.water.id,
        })
        line = waybill.transportable_line_ids
        line._onchange_transportable_id()
        self.assertEqual(
            line.name, self.water.name)
        self.assertEqual(
            line.transportable_uom_id, self.water.uom_id)
