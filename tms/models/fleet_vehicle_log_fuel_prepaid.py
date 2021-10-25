# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FleetVehicleLogFuelPrepaid(models.Model):
    _name = 'fleet.vehicle.log.fuel.prepaid'
    _description = 'Prepaid Fuel Vouchers'

    name = fields.Char()
    price_total = fields.Float(string='Total')
    invoice_id = fields.Many2one(
        'account.move', string='Invoice', readonly=True)
    invoice_paid = fields.Boolean(
        compute='_compute_invoiced_paid')
    operating_unit_id = fields.Many2one(
        'operating.unit')
    notes = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed')],
        readonly=True,
        default='draft')
    vendor_id = fields.Many2one('res.partner', string="Supplier")
    date = fields.Date(
        required=True,
        default=fields.Date.context_today)
    product_id = fields.Many2one(
        'product.product',
        domain=[('tms_product_category', '=', 'fuel')])
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    log_fuel_ids = fields.One2many(
        'fleet.vehicle.log.fuel',
        'prepaid_id',
        string='Fuel Vauchers',
        readonly=True,
    )
    balance = fields.Float(readonly=True, compute="_compute_balance")

    @api.model
    def create(self, values):
        res = super().create(values)
        if not res.operating_unit_id.prepaid_fuel_sequence_id:
            raise ValidationError(
                _('You need to define the sequence for fuel logs in base %s')
                % res.operating_unit_id.name)
        sequence = res.operating_unit_id.prepaid_fuel_sequence_id
        res.name = sequence.next_by_id()
        return res

    @api.depends('log_fuel_ids')
    def _compute_balance(self):
        for rec in self:
            balance = rec.price_total
            for fuel in rec.log_fuel_ids:
                balance -= fuel.price_total
                if balance > rec.price_total:
                    raise ValidationError(
                        _('The total amount of fuel voucher is '
                          'higher than the allowed limit'))
            rec.balance = balance

    @api.depends('invoice_id')
    def _compute_invoiced_paid(self):
        for rec in self:
            invoice_paid = False
            if rec.invoice_id and rec.invoice_id.state == "paid":
                invoice_paid = True
            rec.invoice_paid = invoice_paid

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def create_invoice(self):
        if self.mapped('invoice_id'):
            raise ValidationError(_('The record is already invoiced'))
        obj_invoice = self.env['account.move']
        for rec in self:
            journal_id = rec.operating_unit_id.purchase_journal_id.id
            fpos = rec.vendor_id.property_account_position_id
            account = rec.product_id.get_product_accounts(fpos)['expense']
            if not account['expense']:
                raise ValidationError(
                    _('You must have an income account in the '
                      'product or its category.'))
            invoice_id = obj_invoice.create({
                'partner_id': rec.vendor_id.id,
                'operating_unit_id': rec.operating_unit_id.id,
                'fiscal_position_id': fpos.id,
                'journal_id': journal_id,
                'currency_id': rec.currency_id.id,
                'type': 'in_invoice',
                'invoice_line_ids': [(0, 0, {
                    'product_id': rec.product_id.id,
                    'quantity': 1,
                    'price_unit': rec.price_total,
                    'uom_id': rec.product_id.uom_id.id,
                    'name': rec.name,
                    'account_id': account.id,
                })]
            })
            rec.write({'invoice_id': invoice_id.id})
            message = _(
                '<strong>Invoice of:</strong> %s </br>') % (rec.name)
            invoice_id.message_post(body=message)

            return {
                'name': 'Customer Invoice',
                'view_mode': 'form',
                'target': 'current',
                'res_model': 'account.move',
                'res_id': invoice_id.id,
                'type': 'ir.actions.act_window'
            }
