# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TmsExpenseLine(models.Model):
    _name = 'tms.expense.line'
    _description = 'Expense Line'

    loan_id = fields.Many2one('tms.expense.loan', string='Loan')
    travel_id = fields.Many2one(
        'tms.travel')
    expense_id = fields.Many2one(
        'tms.expense')
    product_qty = fields.Float(
        string='Qty', default=1.0)
    unit_price = fields.Float()
    price_subtotal = fields.Float(
        compute='_compute_price_subtotal',
        string='Subtotal',)
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure')
    line_type = fields.Selection(
        [('real_expense', 'Real Expense'),
         ('made_up_expense', 'Made-up Expense'),
         ('salary', 'Salary'),
         ('fuel', 'Fuel'),
         ('fuel_cash', 'Fuel in Cash'),
         ('refund', 'Refund'),
         ('salary_retention', 'Salary Retention'),
         ('salary_discount', 'Salary Discount'),
         ('other_income', 'Other Income'),
         ('tollstations', 'Toll Stations'),
         ('loan', 'Loan')],
        compute='_compute_line_type',
        store=True, readonly=True)
    name = fields.Char(
        'Description',
        required=True)
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of "
        "sales order lines.",
        default=10)
    price_total = fields.Float(
        string='Total',
        compute='_compute_price_total',
    )
    tax_amount = fields.Float(
        compute='_compute_tax_amount',)
    special_tax_amount = fields.Float(
        string='Special Tax'
    )
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain=[('type_tax_use', '=', 'purchase')])
    notes = fields.Text()
    employee_id = fields.Many2one(
        'hr.employee',
        string='Driver')
    date = fields.Date()
    state = fields.Char(readonly=True)
    control = fields.Boolean()
    automatic = fields.Boolean(
        help="Check this if you want to create Advances and/or "
        "Fuel Vouchers for this line automatically")
    is_invoice = fields.Boolean(string='Is Invoice?')
    partner_id = fields.Many2one(
        'res.partner', string='Supplier',)
    invoice_date = fields.Date()
    invoice_number = fields.Char()
    invoice_id = fields.Many2one(
        'account.move',
        string='Supplier Invoice')
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,)
    route_id = fields.Many2one(
        'tms.route', related='travel_id.route_id',
        string='Route', readonly=True)
    expense_fuel_log = fields.Boolean(readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.line_type not in [
                'salary', 'salary_retention', 'salary_discount']:
            self.tax_ids = self.product_id.supplier_taxes_id
        self.line_type = self.product_id.tms_product_category
        self.product_uom_id = self.product_id.uom_id.id
        self.name = self.product_id.name

    @api.depends('product_id')
    def _compute_line_type(self):
        for rec in self:
            rec.line_type = rec.product_id.tms_product_category

    @api.depends('tax_ids', 'product_qty', 'unit_price')
    def _compute_tax_amount(self):
        for rec in self:
            taxes = rec.tax_ids.compute_all(
                rec.unit_price, rec.expense_id.currency_id,
                rec.product_qty,
                rec.expense_id.employee_id.sudo().address_home_id)
            if taxes['taxes']:
                for tax in taxes['taxes']:
                    rec.tax_amount += tax['amount']
            else:
                rec.tax_amount = 0.0

    @api.depends('product_qty', 'unit_price', 'line_type')
    def _compute_price_subtotal(self):
        for rec in self:
            if rec.line_type in [
                    'salary_retention', 'salary_discount', 'loan']:
                rec.price_subtotal = rec.product_qty * rec.unit_price * -1
            elif rec.line_type == 'fuel':
                rec.price_subtotal = rec.unit_price
            else:
                rec.price_subtotal = rec.product_qty * rec.unit_price

    @api.depends('price_subtotal', 'tax_ids')
    def _compute_price_total(self):
        for rec in self:
            if rec.line_type == 'fuel':
                rec.price_total = rec.unit_price
            elif rec.line_type in [
                    'salary_retention', 'salary_discount', 'loan']:
                rec.price_total = rec.price_subtotal - rec.tax_amount
            else:
                rec.price_total = rec.price_subtotal + rec.tax_amount

    @api.model
    def create(self, values):
        expense_line = super().create(values)
        if expense_line.line_type in (
                'salary_discount', 'salary_retention', 'loan'):
            if expense_line.price_total > 0:
                raise ValidationError(_('This line type needs a '
                                        'negative value to continue!'))
        return expense_line
