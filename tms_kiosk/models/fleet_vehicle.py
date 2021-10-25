# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model
    def vehicle_scan(self, barcode):
        """ Receive a barcode scanned from the Kiosk Mode
            and show the corresponding vehicle.
            Returns either an action or a warning.
        """
        vehicle = self.search(
            ['|', ('name', '=', barcode), ('vin_sn', '=', barcode)], limit=1)
        if not vehicle:
            return {
                'warning': _(
                    'No vehicle corresponding to barcode %s') % barcode
            }
        extradata = []
        datas = vehicle.unit_extradata.filtered(lambda r: r.can_be_sanned)
        for data in datas:
            extradata.append({
                'id': data.id,
                'name': data.type_id.name,
            })
        return {
            'action': {
                'type': 'ir.actions.client',
                'tag': 'tms_kiosk_vehicle',
                'target': 'fullscreen',
                'params': {
                    'id': vehicle.id,
                    'name': vehicle.name,
                    'extradata': extradata,
                },
            }
        }
