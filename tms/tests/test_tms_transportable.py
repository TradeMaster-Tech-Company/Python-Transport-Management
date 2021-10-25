# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestTmsTransportable(TransactionCase):

    def setUp(self):
        super().setUp()
        self.obj_transportable = self.env['tms.transportable']
        self.ton = self.env.ref('uom.product_uom_ton')
        self.transportable = self.env.ref('tms.tms_transportable_01')

    @mute_logger('openerp.sql_db')
    def _test_10_tms_transportable_product_unique_name(self):
        # Catch correctly the IntegrityError
        with self.assertRaisesRegex(
                IntegrityError,
                'duplicate key value violates unique constraint '
                '"tms_transportable_name_unique"'):
            self.obj_transportable.create(
                {'name': 'Test', 'uom_id': self.ton.id})
            self.obj_transportable.create(
                {'name': 'Test', 'uom_id': self.ton.id})

    def test_20_tms_transportable_copy(self):
        transportable = self.transportable.copy()
        self.assertEqual(transportable.name, 'Copy of [Sand]')
        transportable2 = self.transportable.copy()
        self.assertEqual(transportable2.name, 'Copy of [Sand, 1]')
