# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TmsWaybillTaxes(models.Model):
    _name = "tms.waybill.taxes"
    _description = "Waybill Taxes"
    _order = "tax_amount desc"

    waybill_id = fields.Many2one('tms.waybill', 'Waybill', readonly=True)
    tax_id = fields.Many2one('account.tax', 'Tax', readonly=True)
    account_id = fields.Many2one(
        'account.account', 'Tax Account', required=False,
        domain=[('type', '<>', 'view'),
                ('type', '<>', 'income'),
                ('type', '<>', 'closed')])
    account_analytic_id = fields.Many2one(
        'account.analytic.account', 'Analytic account')
    tax_amount = fields.Float(digits='Account', readonly=True)
