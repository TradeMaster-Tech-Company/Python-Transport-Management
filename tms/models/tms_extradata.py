# © <2012> <Israel Cruz Argil, Argil Consulting>
# © <2016> <Jarsa Sistemas, S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import api, fields, models


class TmsExtradata(models.Model):
    _name = "tms.extradata"
    _description = "TMS Extra Data"

    type_id = fields.Many2one(
        'tms.extradata.type', string="Type of Data", required="True")
    type = fields.Selection(related="type_id.type")
    value_char = fields.Char()
    value_integer = fields.Integer()
    value_float = fields.Float()
    value_date = fields.Date()
    value_datetime = fields.Datetime()
    value_extra = fields.Text()
    waybill_id = fields.Many2one(
        'tms.waybill', 'Waybill',
        ondelete='cascade')
    vehicle_id = fields.Many2one(
        'fleet.vehicle', 'Vehicle',
        ondelete='cascade')

    @api.onchange('value_char', 'value_integer', 'value_float',
                  'value_date', 'value_datetime', 'value_extra')
    def onchange_value(self):
        values = [
            ['char', self.value_char],
            ['integer', str(self.value_integer)],
            ['float', str(self.value_float)],
            ['date', self.value_date],
            ['datetime', self.value_datetime]
        ]
        for value in values:
            if self.type == value[0]:
                self.value_extra = value[1]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])  # pylint: disable=c-extension-no-member
        active_model = self._context['active_model_base']
        for node in doc.xpath("//field[@name='type_id']"):
            if active_model == 'fleet.vehicle':
                node.set('domain', "[('apply_on', '=', 'unit')]")
            elif active_model == 'tms.waybill':
                node.set('domain', "[('apply_on', '=', 'waybill')]")
        res['arch'] = (
            etree.tostring(doc))  # pylint: disable=c-extension-no-member
        return res
