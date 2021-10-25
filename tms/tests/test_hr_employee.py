# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from mock import MagicMock

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
try:
    from sodapy import Socrata
except ImportError:
    _logger.debug('Cannot `import sodapy`.')


class TestHrEmployee(TransactionCase):

    def setUp(self):
        super().setUp()
        self.employee_id = self.env.ref('tms.tms_hr_employee_01')
        self.response = [
            {
                'categoria_de_la_licencia': 'CATEGORIA A',
                'fecha_fin_vigencia': '2017-06-26T00:00:00.000',
                'fecha_inicio_vigencia': '2012-06-26T00:00:00.000',
                'licencia': 'QROO002722'},
            {
                'categoria_de_la_licencia': 'CATEGORIA A',
                'fecha_fin_vigencia': '2100-11-13T00:00:00.000',
                'fecha_inicio_vigencia': '2098-11-13T00:00:00.000',
                'licencia': 'QROO002722'},
            {
                'categoria_de_la_licencia': 'CATEGORIA A',
                'fecha_fin_vigencia': '2102-11-13T00:00:00.000',
                'fecha_inicio_vigencia': '2100-11-13T00:00:00.000',
                'licencia': 'QROO002722'}]

    def test_10_compute_days_to_expire(self):
        self.employee_id.update({
            'license_expiration': False,
        })
        self.assertEqual(self.employee_id.days_to_expire, 0)

    def test_20_get_driver_license_info(self):
        Socrata.__init__ = MagicMock(return_value=None)
        Socrata.session = MagicMock()
        Socrata.session.close = MagicMock()
        Socrata.get = MagicMock(return_value=self.response)
        self.employee_id.get_driver_license_info()
        self.assertEqual(self.employee_id.license_type, 'CATEGORIA A')
        self.assertEqual(self.employee_id.license_valid_from.strftime(
            '%Y-%m-%d'), '2012-06-26')
        self.assertEqual(self.employee_id.license_expiration.strftime(
            '%Y-%m-%d'), '2017-06-26')
        Socrata.get.return_value = False
        with self.assertRaisesRegex(
                ValidationError,
                'The driver license is not in SCT database'):
            self.employee_id.get_driver_license_info()
