# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
try:
    from num2words import num2words
except ImportError:
    _logger.debug('Cannot `import num2words`.')


class FleetVehicleLogFuel(models.Model):
    _name = 'fleet.vehicle.log.fuel'
    _inherit = ['mail.thread']
    _description = 'Fuel Logs'
    _order = "date desc,vehicle_id desc"

    name = fields.Char()
    travel_id = fields.Many2one('tms.travel')
    expense_id = fields.Many2one('tms.expense')
    employee_id = fields.Many2one(
        'hr.employee',
        string='Driver',
        domain=[('driver', '=', True)],
        related='travel_id.employee_id',
        store=True,)
    vehicle_id = fields.Many2one('fleet.vehicle', required=True,)
    date = fields.Date(required=True, default=fields.Date.today)
    odometer = fields.Float(related='vehicle_id.odometer',)
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    product_qty = fields.Float(string='Liters', default=1.0,)
    tax_amount = fields.Float(string='Taxes',)
    price_total = fields.Float(string='Total')
    special_tax_amount = fields.Float(
        compute="_compute_special_tax_amount", string='IEPS')
    price_unit = fields.Float(
        compute='_compute_price_unit', string='Unit Price')
    price_subtotal = fields.Float(
        string="Subtotal", compute='_compute_price_subtotal')
    invoice_id = fields.Many2one(
        'account.move', string='Invoice', readonly=True)
    invoice_paid = fields.Boolean(
        compute='_compute_invoiced_paid')
    operating_unit_id = fields.Many2one(
        'operating.unit', string='Operating Unit')
    notes = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled')],
        readonly=True,
        tracking=True,
        default='draft')
    vendor_id = fields.Many2one('res.partner', required=True,)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain=[('tms_product_category', '=', 'fuel')])
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    ticket_number = fields.Char()
    prepaid_id = fields.Many2one(
        'fleet.vehicle.log.fuel.prepaid',
        string='Prepaid',
        compute="_compute_prepaid"
    )
    created_from_expense = fields.Boolean(readonly=True)
    expense_line_id = fields.Many2one('tms.expense.line', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)

    @api.depends('vendor_id')
    def _compute_prepaid(self):
        obj_prepaid = self.env['fleet.vehicle.log.fuel.prepaid']
        for rec in self:
            prepaid_id = obj_prepaid.search([
                ('operating_unit_id', '=', rec.operating_unit_id.id),
                ('vendor_id', '=', rec.vendor_id.id),
                ('state', '=', 'confirmed')], limit=1, order="date")
            if prepaid_id:
                if prepaid_id.balance > rec.price_total:
                    rec.prepaid_id = prepaid_id.id
                else:
                    # TODO Remove raise
                    raise ValidationError(
                        _('Insufficient amount'))
            rec.prepaid_id = False

    @api.depends('tax_amount')
    def _compute_price_subtotal(self):
        for rec in self:
            price_subtotal = 0
            if rec.tax_amount > 0:
                price_subtotal = rec.tax_amount / 0.16
            rec.price_subtotal = price_subtotal

    @api.depends('product_qty', 'price_subtotal')
    def _compute_price_unit(self):
        for rec in self:
            price_unit = 0
            if rec.product_qty and rec.price_subtotal > 0:
                price_unit = rec.price_subtotal / rec.product_qty
            rec.price_unit = price_unit

    @api.depends('price_subtotal', 'tax_amount', 'price_total')
    def _compute_special_tax_amount(self):
        for rec in self:
            special_tax_amount = 0
            if rec.price_subtotal and rec.price_total and rec.tax_amount > 0:
                special_tax_amount = (
                    rec.price_total - rec.price_subtotal - rec.tax_amount)
            rec.special_tax_amount = special_tax_amount

    def action_approved(self):
        for rec in self:
            rec.state = 'approved'

    def action_cancel(self):
        if self.mapped('invoice_id'):
            raise ValidationError(
                _('Could not cancel Fuel Voucher! This Fuel Voucher is '
                  'already Invoiced'))
        for rec in self:
            if (rec.travel_id and rec.travel_id.state == 'closed'):
                raise ValidationError(
                    _('Could not cancel Fuel Voucher! This Fuel '
                      'Voucher is already linked to a Travel Expense'))
            rec.state = 'cancel'

    @api.model
    def create(self, values):
        res = super().create(values)
        if not res.operating_unit_id.fuel_log_sequence_id:
            raise ValidationError(
                _('You need to define the sequence for fuel logs in base %s') %
                res.operating_unit_id.name)
        sequence = res.operating_unit_id.fuel_log_sequence_id
        res.name = sequence.next_by_id()
        return res

    def set_2_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            if (rec.product_qty <= 0 or
                    rec.tax_amount <= 0 or
                    rec.price_total <= 0):
                raise ValidationError(
                    _('Liters, Taxes and Total'
                      ' must be greater than zero.'))
            rec.state = 'confirmed'

    @api.onchange('travel_id')
    def _onchange_travel(self):
        self.vehicle_id = self.travel_id.unit_id
        self.employee_id = self.travel_id.employee_id

    @api.depends('invoice_id')
    def _compute_invoiced_paid(self):
        for rec in self:
            rec.invoice_paid = (
                rec.invoice_id and
                rec.invoice_id.invoice_payment_state == 'paid')

    def _amount_to_text(self, product_qty):
        # TODO Use the Odoo method in the currency
        total = str(float(product_qty)).split('.')[0]
        total = num2words(float(total), lang='es').upper()
        return '%s' % (total)
