# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class TmsExtradata(models.Model):
    _inherit = 'tms.extradata'

    can_be_sanned = fields.Boolean()

    @api.model
    def data_scan(self, barcode, vehicle_id):
        """ Receive a barcode scanned from the Kiosk Mode
            and show the corresponding data.
            Returns data or a warning.
        """
        data = self.search(
            [('value_extra', '=', barcode), ('vehicle_id', '=', vehicle_id)])
        if not data:
            return {
                'warning': _(
                    'No data corresponding to barcode %s') % barcode
            }
        return {
            'data': {
                'id': data.id,
            }
        }
