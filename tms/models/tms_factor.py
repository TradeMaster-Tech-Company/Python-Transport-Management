# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TmsFactor(models.Model):
    _name = "tms.factor"
    _description = "Factors to calculate Payment (Driver/Supplier) "
    "& Client charge"
    _order = "sequence"

    name = fields.Char(required=True)
    route_id = fields.Many2one('tms.route', string="Route")
    travel_id = fields.Many2one('tms.travel', string='Travel')
    waybill_id = fields.Many2one(
        'tms.waybill', string='waybill',
        index=True, readonly=True)
    category = fields.Selection([
        ('driver', 'Driver'),
        ('customer', 'Customer'),
        ('supplier', 'Supplier')], 'Type', required=True)
    factor_type = fields.Selection([
        ('distance', 'Distance Route (Km/Mi)'),
        ('distance_real', 'Distance Real (Km/Mi)'),
        ('weight', 'Weight'),
        ('travel', 'Travel'),
        ('qty', 'Quantity'),
        ('volume', 'Volume'),
        ('percent', 'Income Percent'),
        ('percent_driver', 'Income Percent per Driver'),
        ('amount_driver', 'Amount Percent per Driver')],
        required=True,
        help='For next options you have to type Ranges or Fixed Amount\n - '
             'Distance Route (Km/mi)\n - Distance Real (Km/Mi)\n - Weight\n'
             ' - Quantity\n - Volume\nFor next option you only have to type'
             ' Fixed Amount:\n - Travel\nFor next option you only have to type'
             ' Factor like 10.5 for 10.50%:\n - Income Percent')
    range_start = fields.Float()
    range_end = fields.Float()
    factor = fields.Float()
    fixed_amount = fields.Float()
    mixed = fields.Boolean()
    sequence = fields.Integer(
        help="Gives the sequence calculation for these factors.",
        default=10)
    notes = fields.Text()

    @api.onchange('factor_type')
    def _onchange_factor_type(self):
        values = {
            'distance': _('Distance Route (Km/Mi)'),
            'distance_real': _('Distance Real (Km/Mi)'),
            'weight': _('Weight'),
            'travel': _('Travel'),
            'qty': _('Quantity'),
            'volume': _('Volume'),
            'percent': _('Income Percent'),
            'percent_driver': _('Income Percent per Driver'),
            'amount_driver': _('Amount Percent per Driver'),
        }
        self.name = values.get(self.factor_type)

    def get_driver_amount(self, employee, driver_value, amount):
        if not employee:
            raise ValidationError(_(
                'Invalid parameter you can '
                'use this factor only with drivers'))
        if employee.income_percentage == 0.0:
            raise ValidationError(_(
                'The employee must have a income '
                'percentage value'))
        amount += driver_value * (employee.income_percentage / 100)
        return amount

    def get_amount(self, weight=0.0, distance=0.0, distance_real=0.0, qty=0.0,
                   volume=0.0, income=0.0, employee=False):
        factor_list = {'weight': weight, 'distance': distance,
                       'distance_real': distance_real, 'qty': qty,
                       'volume': volume}
        amount = 0.0
        for rec in self:
            if rec.factor_type == 'travel':
                amount += rec.fixed_amount
            elif rec.factor_type == 'percent':
                amount += income * (rec.factor / 100)
            elif rec.factor_type == 'percent_driver':
                amount += rec.get_driver_amount(
                    employee, income, amount)
            elif rec.factor_type == 'amount_driver':
                amount += rec.get_driver_amount(
                    employee, rec.fixed_amount, amount)
            else:
                for key, value in factor_list.items():
                    if rec.factor_type == key:
                        if rec.range_start <= value <= rec.range_end:
                            amount += rec.factor * value
                        elif rec.range_start == 0 and rec.range_end == 0:
                            amount += rec.factor * value
                if amount == 0.0:
                    raise ValidationError(
                        _('the amount isnt between of any ranges'))
            if rec.mixed:
                amount += rec.fixed_amount
        return amount
