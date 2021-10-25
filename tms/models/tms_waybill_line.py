# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division

from odoo import api, fields, models


class TmsWaybillLine(models.Model):
    _name = 'tms.waybill.line'
    _description = 'Waybill Line'
    _order = 'sequence, id desc'

    waybill_id = fields.Many2one(
        'tms.waybill',
        readonly=True)
    name = fields.Char('Description', required=True)
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of "
        "sales order lines.",
        default=10)
    product_id = fields.Many2one(
        'product.product',
        required=True)
    unit_price = fields.Float(
        default=0.0)
    price_subtotal = fields.Float(
        compute='_compute_amount_line',
        string='Subtotal')
    tax_amount = fields.Float(compute='_compute_amount_line')
    tax_ids = fields.Many2many(
        'account.tax', string='Taxes',
        domain='[("type_tax_use", "=", "sale")]')
    product_qty = fields.Float(
        string='Quantity',
        default=1.0)
    discount = fields.Float(
        string='Discount (%)',
        help="Please use 99.99 format...")
    account_id = fields.Many2one(
        'account.account')

    @api.onchange('product_id')
    def on_change_product_id(self):
        for rec in self:
            rec.name = rec.product_id.name
            fpos = rec.waybill_id.partner_id.property_account_position_id
            fpos_tax_ids = fpos.map_tax(rec.product_id.taxes_id)
            rec.tax_ids = fpos_tax_ids
            rec.write({
                'account_id': rec.product_id.property_account_income_id.id
            })

    @api.depends('product_qty', 'unit_price', 'discount')
    def _compute_amount_line(self):
        for rec in self:
            price_discount = (
                rec.unit_price * ((100.00 - rec.discount) / 100))
            taxes = rec.tax_ids.compute_all(
                price_discount, rec.waybill_id.currency_id,
                rec.product_qty, rec.product_id,
                rec.waybill_id.partner_id)
            rec.price_subtotal = taxes['total_excluded']
            rec.tax_amount = taxes['total_included'] - taxes['total_excluded']
