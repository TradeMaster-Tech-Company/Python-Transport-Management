# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division

from datetime import datetime
import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TmsExpense(models.Model):
    _name = 'tms.expense'
    _inherit = 'mail.thread'
    _description = 'Travel Expenses'
    _order = 'name desc'

    name = fields.Char(readonly=True)
    operating_unit_id = fields.Many2one(
        'operating.unit', required=True)
    employee_id = fields.Many2one(
        'hr.employee', 'Driver', required=True,)
    travel_ids = fields.Many2many(
        'tms.travel',
        string='Travels')
    unit_id = fields.Many2one(
        'fleet.vehicle', required=True)
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled')], 'Expense State', readonly=True,
        tracking=True,
        help="Gives the state of the Travel Expense. ",
        default='draft')
    date = fields.Date(required=True, default=fields.Date.context_today)
    expense_line_ids = fields.One2many(
        'tms.expense.line', 'expense_id', 'Expense Lines')
    amount_real_expense = fields.Float(
        compute='_compute_amount_real_expense',
        string='Expenses',
        store=True)
    amount_made_up_expense = fields.Float(
        compute='_compute_amount_made_up_expense',
        string='Fake Expenses',
        store=True)
    fuel_qty = fields.Float(
        compute='_compute_fuel_qty',
        store=True)
    amount_fuel = fields.Float(
        compute='_compute_amount_fuel',
        string='Cost of Fuel',
        store=True)
    amount_fuel_cash = fields.Float(
        compute='_compute_amount_fuel_cash',
        string='Fuel in Cash',
        store=True)
    amount_refund = fields.Float(
        compute='_compute_amount_refund',
        string='Refund',
        store=True)
    amount_other_income = fields.Float(
        compute='_compute_amount_other_income',
        string='Other Income',
        store=True)
    amount_salary = fields.Float(
        compute='_compute_amount_salary',
        string='Salary',
        store=True)
    amount_net_salary = fields.Float(
        compute='_compute_amount_net_salary',
        string='Net Salary',
        store=True)
    amount_salary_retention = fields.Float(
        compute='_compute_amount_salary_retention',
        string='Salary Retentions',
        store=True)
    amount_salary_discount = fields.Float(
        compute='_compute_amount_salary_discount',
        string='Salary Discounts',
        store=True)
    amount_loan = fields.Float(
        compute='_compute_amount_loan',
        string='Total Loans',
        store=True)
    amount_advance = fields.Float(
        compute='_compute_amount_advance',
        string='Total Advances',
        store=True)
    amount_balance = fields.Float(
        compute='_compute_amount_balance',
        string='Balance',
        store=True)
    amount_tax_total = fields.Float(
        compute='_compute_amount_tax_total',
        string='Taxes (All)',
        store=True)
    amount_tax_real = fields.Float(
        compute='_compute_amount_tax_real',
        string='Taxes (Real)',
        store=True)
    amount_total_real = fields.Float(
        compute='_compute_amount_total_real',
        string='Total (Real)',
        store=True)
    amount_total_total = fields.Float(
        compute='_compute_amount_total_total',
        string='Total (All)',
        store=True)
    amount_subtotal_real = fields.Float(
        compute='_compute_amount_subtotal_real',
        string='SubTotal (Real)',
        store=True)
    amount_subtotal_total = fields.Float(
        string='SubTotal (All)',
        compute='_compute_amount_subtotal_total',
        store=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    last_odometer = fields.Float('Last Read')
    vehicle_odometer = fields.Float()
    current_odometer = fields.Float(
        string='Current Real',
        related='unit_id.odometer')
    odometer_log_id = fields.Many2one(
        'fleet.vehicle.odometer', 'Odometer Record')
    notes = fields.Text()
    move_id = fields.Many2one(
        'account.move', 'Journal Entry', readonly=True,
        help="Link to the automatically generated Journal Items.",
        ondelete='restrict',)
    paid = fields.Boolean(
        compute='_compute_paid',
        store=True,
        readonly=True)
    advance_ids = fields.One2many(
        'tms.advance', 'expense_id', string='Advances', readonly=True)
    loan_ids = fields.One2many('tms.expense.loan', 'expense_id',
                               string='Loans', readonly=True)
    fuel_qty_real = fields.Float(
        help="Fuel Qty computed based on Distance Real and Global Fuel "
        "Efficiency Real obtained by electronic reading and/or GPS")
    fuel_diff = fields.Float(
        string="Fuel Difference",
        help="Fuel Qty Difference between Fuel Vouchers + Fuel Paid in Cash "
        "versus Fuel qty computed based on Distance Real and Global Fuel "
        "Efficiency Real obtained by electronic reading and/or GPS"
    )
    fuel_log_ids = fields.One2many(
        'fleet.vehicle.log.fuel', 'expense_id', string='Fuel Vouchers')
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    fuel_efficiency = fields.Float(
        readonly=True,
        compute="_compute_fuel_efficiency")
    payment_move_id = fields.Many2one(
        'account.move', string='Payment Entry',
        readonly=True,)
    travel_days = fields.Char(
        compute='_compute_travel_days',
    )
    distance_loaded = fields.Float(
        compute='_compute_distance_expense',
    )
    distance_empty = fields.Float(
        compute='_compute_distance_expense',
    )
    distance_loaded_real = fields.Float()
    distance_empty_real = fields.Float()
    distance_routes = fields.Float(
        compute='_compute_distance_routes',
        string='Distance from routes',
        help="Routes Distance", readonly=True)
    distance_real = fields.Float(
        help="Route obtained by electronic reading and/or GPS")
    income_km = fields.Float(
        compute='_compute_income_km',
    )
    expense_km = fields.Float(
        compute='_compute_expense_km',
    )
    percentage_km = fields.Float(
        'Productivity Percentage',
        compute='_compute_percentage_km',
    )
    fuel_efficiency_real = fields.Float()
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)

    def _get_time(self, date):
        user = self.env.user
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        start = pytz.utc.localize(date).astimezone(tz)
        return start.strftime("%Y-%m-%d %H:%M:%S")

    @api.depends('travel_ids')
    def _compute_income_km(self):
        for rec in self:
            subtotal_waybills = sum(
                rec.mapped('travel_ids.waybill_ids.amount_untaxed'))
            try:
                rec.income_km = subtotal_waybills / rec.distance_real
            except ZeroDivisionError:
                rec.income_km = 0.0

    @api.depends('distance_real', 'amount_subtotal_real')
    def _compute_expense_km(self):
        for rec in self:
            try:
                rec.expense_km = rec.amount_subtotal_real / rec.distance_real
            except ZeroDivisionError:
                rec.expense_km = 0.0

    @api.depends('income_km', 'expense_km')
    def _compute_percentage_km(self):
        for rec in self:
            try:
                rec.percentage_km = rec.income_km / rec.expense_km
            except ZeroDivisionError:
                rec.percentage_km = 0.0

    @api.depends('travel_ids')
    def _compute_distance_expense(self):
        for rec in self:
            rec.distance_loaded = sum(rec.travel_ids.mapped('distance_loaded'))
            rec.distance_empty = sum(rec.travel_ids.mapped('distance_empty'))

    @api.depends('start_date', 'end_date')
    def _compute_travel_days(self):
        rec_with_date = self.filtered(
            lambda exp: exp.start_date and exp.end_date)
        for rec in self - rec_with_date:
            rec.travel_days = '-'
        for rec in rec_with_date:
            date_start = self._get_time(rec.start_date)
            date_end = self._get_time(rec.end_date)
            strp_start_date = datetime.strptime(
                date_start, "%Y-%m-%d %H:%M:%S")
            strp_end_date = datetime.strptime(
                date_end, "%Y-%m-%d %H:%M:%S")
            difference = strp_end_date - strp_start_date
            days = int(difference.days) + 1
            hours = int(difference.seconds / 3600)
            mins = int((difference.seconds - (hours * 3600)) / 60)
            seconds = difference.seconds - ((hours * 3600) + (mins * 60))
            if hours < 10:
                hours = '0' + str(hours)
            if mins < 10:
                mins = '0' + str(mins)
            if seconds < 10:
                seconds = '0' + str(seconds)
            total_string = (
                str(days) + _('Day(s), ') +
                str(hours) + ':' +
                str(mins) + ':' +
                str(seconds))
            rec.travel_days = total_string

    @api.depends('payment_move_id')
    def _compute_paid(self):
        for rec in self:
            paid = False
            if rec.payment_move_id:
                paid = True
            rec.paid = paid

    @api.depends('fuel_qty', 'distance_real')
    def _compute_fuel_efficiency(self):
        for rec in self:
            fuel_efficiency = 0
            if rec.distance_real and rec.fuel_qty:
                fuel_efficiency = rec.distance_real / rec.fuel_qty
            rec.fuel_efficiency = fuel_efficiency

    @api.depends('expense_line_ids')
    def _compute_fuel_qty(self):
        for rec in self:
            rec.fuel_qty = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'fuel').mapped('product_qty'))

    @api.depends('travel_ids', 'expense_line_ids')
    def _compute_amount_fuel(self):
        for rec in self:
            amount_fuel = 0.0
            for line in rec.fuel_log_ids:
                amount_fuel += (
                    line.price_subtotal +
                    line.special_tax_amount)
            rec.amount_fuel = amount_fuel

    @api.depends('expense_line_ids')
    def _compute_amount_fuel_cash(self):
        # TODO - Why not only one method for all the amounts?
        for rec in self:
            amount_fuel_cash = 0.0
            for line in rec.expense_line_ids.filtered(
                    lambda l: l.line_type == 'fuel_cash'):
                amount_fuel_cash += (
                    line.price_subtotal +
                    line.special_tax_amount)
            rec.amount_fuel_cash = amount_fuel_cash

    @api.depends('expense_line_ids')
    def _compute_amount_refund(self):
        for rec in self:
            rec.amount_refund = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'refund').mapped('price_total'))

    @api.depends('expense_line_ids')
    def _compute_amount_other_income(self):
        for rec in self:
            rec.amount_other_income = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'other_income').mapped('price_total'))

    @api.depends('expense_line_ids')
    def _compute_amount_salary(self):
        for rec in self:
            rec.amount_salary = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'salary').mapped('price_total'))

    @api.depends('expense_line_ids')
    def _compute_amount_salary_discount(self):
        for rec in self:
            rec.amount_salary_discount = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'salary_discount').mapped(
                'price_total'))

    @api.depends('expense_line_ids')
    def _compute_amount_loan(self):
        for rec in self:
            rec.amount_loan = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'loan').mapped('price_total'))

    @api.depends('expense_line_ids')
    def _compute_amount_made_up_expense(self):
        for rec in self:
            rec.amount_made_up_expense = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'made_up_expense').mapped(
                'price_total'))

    @api.depends('expense_line_ids')
    def _compute_amount_real_expense(self):
        for rec in self:
            rec.amount_real_expense = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'real_expense').mapped(
                'price_subtotal'))

    @api.depends('travel_ids', 'expense_line_ids')
    def _compute_amount_subtotal_real(self):
        for rec in self:
            rec.amount_subtotal_real = (
                rec.amount_salary +
                rec.amount_salary_discount +
                rec.amount_real_expense +
                rec.amount_salary_retention +
                rec.amount_loan +
                rec.amount_refund +
                rec.amount_fuel_cash +
                rec.amount_other_income)

    @api.depends('travel_ids', 'expense_line_ids')
    def _compute_amount_total_real(self):
        for rec in self:
            rec.amount_total_real = (
                rec.amount_subtotal_real +
                rec.amount_tax_real)

    @api.depends('travel_ids', 'expense_line_ids')
    def _compute_amount_balance(self):
        for rec in self:
            rec.amount_balance = (
                rec.amount_total_real - rec.amount_advance)

    @api.depends('travel_ids')
    def _compute_amount_net_salary(self):
        for rec in self:
            rec.amount_net_salary = 1.0

    @api.depends('expense_line_ids')
    def _compute_amount_salary_retention(self):
        for rec in self:
            rec.amount_salary_retention = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'salary_retention').mapped(
                'price_total'))

    @api.depends('travel_ids', 'expense_line_ids')
    def _compute_amount_advance(self):
        for rec in self:
            rec.amount_advance = sum(
                rec.mapped('travel_ids.advance_ids').filtered(
                    lambda a: a.payment_move_id).mapped('amount'))

    @api.depends('travel_ids', 'expense_line_ids', 'amount_tax_real')
    def _compute_amount_tax_total(self):
        for rec in self:
            rec.amount_tax_total = (sum(
                rec.mapped('travel_ids.fuel_log_ids.tax_amount')) +
                rec.amount_tax_real)

    @api.depends('expense_line_ids')
    def _compute_amount_tax_real(self):
        for rec in self:
            rec.amount_tax_real = sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'real_expense').mapped('tax_amount'))

    @api.depends('travel_ids', 'expense_line_ids', 'amount_balance')
    def _compute_amount_subtotal_total(self):
        for rec in self:
            amount_subtotal_total = 0
            for fuel_log in rec.mapped('travel_ids.fuel_log_ids'):
                amount_subtotal_total += (
                    fuel_log.price_subtotal +
                    fuel_log.special_tax_amount)
            amount_subtotal_total += sum(rec.expense_line_ids.filtered(
                lambda l: l.line_type == 'real_expense').mapped(
                'price_subtotal'))
            amount_subtotal_total += rec.amount_balance
            rec.amount_subtotal_total = amount_subtotal_total

    @api.depends('travel_ids', 'expense_line_ids')
    def _compute_amount_total_total(self):
        for rec in self:
            rec.amount_total_total = (
                rec.amount_subtotal_total + rec.amount_tax_total +
                rec.amount_made_up_expense)

    @api.depends('travel_ids')
    def _compute_distance_routes(self):
        for rec in self:
            rec.distance_routes = sum(rec.travel_ids.mapped('distance_route'))

    @api.depends('travel_ids')
    def _compute_distance_real(self):
        for rec in self:
            rec.distance_real = sum(rec.travel_ids.mapped('distance_driver'))

    @api.model
    def create(self, values):
        operating_unit = self.env['operating.unit'].browse(
            values.get('operating_unit_id'))
        sequence = operating_unit.expense_sequence_id
        values['name'] = sequence.next_by_id()
        return super().create(values)

    def write(self, values):
        for rec in self:
            res = super().write(values)
            rec.get_travel_info()
            return res

    def unlink(self):
        if self.filtered(lambda rec: rec.state == 'confirmed'):
            raise ValidationError(
                _('You can not delete a travel expense in status confirmed'))
        for rec in self:
            travels = self.env['tms.travel'].search(
                [('expense_id', '=', rec.id)])
            travels.write({
                'expense_id': False,
                'state': 'done'
            })
            advances = self.env['tms.advance'].search(
                [('expense_id', '=', rec.id)])
            advances.write({
                'expense_id': False,
                'state': 'confirmed'
            })
            fuel_logs = self.env['fleet.vehicle.log.fuel'].search(
                [('expense_id', '=', rec.id)])
            fuel_logs.write({
                'expense_id': False,
                'state': 'confirmed'
            })
            return super().unlink()

    def action_approved(self):
        for rec in self:
            rec.state = 'approved'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model
    def prepare_move_line(self, name, ref, account_id,
                          debit, credit, journal_id,
                          partner_id, operating_unit_id):
        return (0, 0, {
            'name': name,
            'ref': ref,
            'account_id': account_id,
            'debit': debit,
            'credit': credit,
            'journal_id': journal_id,
            'partner_id': partner_id,
            'operating_unit_id': operating_unit_id,
            'company_id': self.env.user.company_id.id,
        })

    @api.model
    def create_fuel_vouchers(self, line):
        for rec in self:
            fuel_voucher = rec.env['fleet.vehicle.log.fuel'].create({
                'operating_unit_id': rec.operating_unit_id.id,
                'travel_id': line.travel_id.id,
                'vehicle_id': (
                    line.travel_id.unit_id.id or line.expense_id.unit_id.id),
                'product_id': line.product_id.id,
                'price_unit': line.unit_price,
                'price_subtotal': line.price_subtotal,
                'vendor_id': line.partner_id.id,
                'product_qty': line.product_qty,
                'tax_amount': line.tax_amount,
                'state': 'closed',
                'employee_id': rec.employee_id.id,
                'price_total': line.price_total,
                'date': line.date,
                'expense_id': rec.id,
                'ticket_number': line.invoice_number,
                'created_from_expense': True,
                'expense_line_id': line.id,
                })
            line.write({'expense_fuel_log': True})
            return fuel_voucher

    def higher_than_zero_move(self):
        for rec in self:
            move_lines = []
            invoices = []
            move_obj = rec.env['account.move']
            journal_id = rec.operating_unit_id.expense_journal_id.id
            advance_account_id = (
                rec.employee_id.
                tms_advance_account_id.id
            )
            negative_account = (
                rec.employee_id.
                tms_expense_negative_account_id.id
            )
            driver_account_payable = (
                rec.employee_id.
                address_home_id.property_account_payable_id.id
            )
            if not journal_id:
                raise ValidationError(
                    _('Warning! The expense does not have a journal'
                      ' assigned. \nCheck if you already set the '
                      'journal for expense moves in the Operating Unit.'))
            if not driver_account_payable:
                raise ValidationError(
                    _('Warning! The driver does not have a home address'
                      ' assigned. \nCheck if you already set the '
                      'home address for the employee.'))
            if not advance_account_id:
                raise ValidationError(
                    _('Warning! You must have configured the accounts'
                        'of the tms for the Driver'))
            # We check if the advance amount is higher than zero to create
            # a move line
            if rec.amount_advance > 0:
                move_line = rec.prepare_move_line(
                    _('Advance Discount'),
                    rec.name,
                    advance_account_id,
                    0.0,
                    rec.amount_advance,
                    journal_id,
                    rec.employee_id.address_home_id.id,
                    rec.operating_unit_id.id)
                move_lines.append(move_line)
            result = {
                'move_lines': move_lines,
                'invoices': invoices,
                'move_obj': move_obj,
                'journal_id': journal_id,
                'advance_account_id': advance_account_id,
                'negative_account': negative_account,
                'driver_account_payable': driver_account_payable
            }
            return result

    def check_expenseline_invoice(self, line, result, product_account):
        for rec in self:
            # We check if the expense line is an invoice to create it
            # and make the move line based in the total with taxes
            inv_id = False
            if line.is_invoice:
                inv_id = rec.create_supplier_invoice(line)
                inv_id.action_post()
                result['invoices'].append(inv_id)
                move_line = rec.prepare_move_line(
                    (rec.name + ' ' + line.name +
                     ' - Inv ID - ' + str(inv_id.id)),
                    (rec.name + ' - Inv ID - ' + str(inv_id.id)),
                    (line.partner_id.
                        property_account_payable_id.id),
                    (line.price_total if line.price_total > 0.0
                        else 0.0),
                    (line.price_total if line.price_total <= 0.0
                        else 0.0),
                    result['journal_id'],
                    line.partner_id.id,
                    rec.operating_unit_id.id)
            # if the expense line not be a invoice we make the move
            # line based in the subtotal
            elif (rec.employee_id.outsourcing and
                  line.product_id.tms_product_category in
                  ['salary', 'other_income', 'salary_discount']):
                continue
            else:
                move_line = rec.prepare_move_line(
                    rec.name + ' ' + line.name,
                    rec.name,
                    product_account,
                    (line.price_subtotal if line.price_subtotal > 0.0
                        else 0.0),
                    (line.price_subtotal * -1.0
                        if line.price_subtotal < 0.0
                        else 0.0),
                    result['journal_id'],
                    rec.employee_id.address_home_id.id,
                    rec.operating_unit_id.id)
            result['move_lines'].append(move_line)
            if line.is_invoice:
                continue
            # we check the line tax to create the move line if
            # the line not be an invoice
            # TODO: Fix this, this only works when the expense has 1 tax
            taxes = line.tax_ids.compute_all(
                line.price_subtotal, rec.currency_id)['taxes']
            for tax in taxes:
                tax_account = tax['account_id']
                tax_amount = line.tax_amount
                # We create a move line for the line tax
                move_line = rec.prepare_move_line(
                    _('Tax Line: %s %s') % (rec.name, line.name),
                    rec.name,
                    tax_account,
                    (tax_amount if tax_amount > 0.0
                        else 0.0),
                    (tax_amount if tax_amount <= 0.0
                        else 0.0),
                    result['journal_id'],
                    rec.employee_id.address_home_id.id,
                    rec.operating_unit_id.id)
                result['move_lines'].append(move_line)

    def create_expense_line_move_line(self, line, result):
        for rec in self:
            # We only need all the lines except the fuel and the
            # made up expenses
            if line.line_type == 'fuel' and (
                    not line.control or line.expense_fuel_log):
                rec.create_fuel_vouchers(line)
            if line.line_type not in (
                    'made_up_expense', 'fuel', 'tollstations'):
                product_account = (
                    result['negative_account']
                    if (line.product_id.
                        tms_product_category == 'negative_balance')
                    else (line.product_id.
                          property_account_expense_id.id)
                    if (line.product_id.
                        property_account_expense_id.id)
                    else (line.product_id.categ_id.
                          property_account_expense_categ_id.id)
                    if (line.product_id.categ_id.
                        property_account_expense_categ_id.id)
                    else False)
                if not product_account:
                    raise ValidationError(
                        _('Warning ! Expense Account is not defined for'
                            ' product %s') % (line.product_id.name))
                self.check_expenseline_invoice(line, result, product_account)

    def check_balance_value(self, result):
        for rec in self:
            balance = rec.amount_balance
            if (rec.employee_id.outsourcing and rec.expense_line_ids.filtered(
                    lambda x: x.line_type in ['other_income', 'salary'])):
                balance = (
                    balance - rec.amount_other_income -
                    rec.amount_salary) - sum(
                    rec.expense_line_ids.filtered(
                        lambda y: y.line_type == 'salary_discount').mapped(
                        'price_total'))
            if balance < 0:
                move_line = rec.prepare_move_line(
                    _('Negative Balance'),
                    rec.name,
                    result['negative_account'],
                    balance * -1.0,
                    0.0,
                    result['journal_id'],
                    rec.employee_id.address_home_id.id,
                    rec.operating_unit_id.id)
            else:
                move_line = rec.prepare_move_line(
                    rec.name,
                    rec.name,
                    result['driver_account_payable'],
                    0.0,
                    balance,
                    result['journal_id'],
                    rec.employee_id.address_home_id.id,
                    rec.operating_unit_id.id)
            result['move_lines'].append(move_line)

    def reconcile_account_move(self, result):
        for rec in self:
            move = {
                'date': fields.Date.today(),
                'journal_id': result['journal_id'],
                'name': rec.name,
                'line_ids': result['move_lines'],
                'operating_unit_id': rec.operating_unit_id.id,
                'company_id': self.env.user.company_id.id,
            }
            move_id = result['move_obj'].create(move)
            if not move_id:
                raise ValidationError(
                    _('An error has occurred in the creation'
                        ' of the accounting move. '))
            move_id.action_post()
            # Here we reconcile the invoices with the corresponding
            # move line
            rec.reconcile_supplier_invoices(result['invoices'], move_id)
            rec.write(
                {
                    'move_id': move_id.id,
                    'state': 'confirmed'
                })

    def action_confirm(self):
        for rec in self:
            if rec.move_id:
                raise ValidationError(
                    _('You can not confirm a confirmed expense.'))
            result = rec.higher_than_zero_move()
            for line in rec.expense_line_ids:
                rec.create_expense_line_move_line(line, result)
            # Here we check if the balance is positive or negative to create
            # the move line with the correct values
            rec.check_balance_value(result)
            rec.reconcile_account_move(result)

    def action_cancel(self):
        self.ensure_one()
        if self.paid:
            raise ValidationError(
                _('You cannot cancel an expense that is paid.'))
        if self.state == 'confirmed':
            for line in self.expense_line_ids:
                if line.invoice_id and line.line_type != 'fuel':
                    for move_line in line.invoice_id.move_id.line_ids:
                        if move_line.account_id.reconcile:
                            move_line.remove_move_reconcile()
                    line.invoice_id.write({
                        # TODO Make a separate module to delete oml data
                        'cfdi_fiscal_folio': False,
                        'xml_signed': False,
                        'reference': False,
                    })
                    line.invoice_id.signal_workflow('invoice_cancel')
                    line.invoice_id = False
            if self.move_id.state == 'posted':
                self.move_id.button_cancel()
            self.move_id = False
            self.fuel_log_ids.filtered(
                lambda x: x.created_from_expense).unlink()
        self.state = 'cancel'

    def unattach_info(self):
        for rec in self:
            exp_no_travel = rec.expense_line_ids.search([
                ('expense_id', '=', rec.id),
                ('travel_id', '=', False)]).ids
            rec.expense_line_ids.search([
                ('expense_id', '=', rec.id),
                ('travel_id', 'not in', rec.travel_ids.ids),
                ('id', 'not in', exp_no_travel)]).unlink()
            rec.expense_line_ids.search([
                ('expense_id', '=', rec.id),
                ('control', '=', True)]).unlink()
            travels = self.env['tms.travel'].search(
                [('expense_id', '=', rec.id)])
            travels.write({'expense_id': False, 'state': 'done'})
            advances = self.env['tms.advance'].search(
                [('expense_id', '=', rec.id)])
            advances.write({
                'expense_id': False,
                'state': 'confirmed'
            })
            fuel_logs = self.env['fleet.vehicle.log.fuel'].search(
                [('expense_id', '=', rec.id),
                 ('created_from_expense', '=', False)])
            fuel_logs.write({
                'expense_id': False,
                'state': 'confirmed',
            })

    def create_advance_line(self, advance, travel):
        if advance.state not in ('confirmed', 'cancel'):
            raise ValidationError(_(
                'Oops! All the advances must be confirmed'
                ' or cancelled \n '
                'Name of advance not confirmed or cancelled: ' +
                advance.name +
                '\n State: ' + advance.state))
        if not advance.paid and advance.state == 'confirmed':
            raise ValidationError(_(
                'Oops! All the advances must be paid'
                '\n Name of advance not paid: ' +
                advance.name))
        if (advance.auto_expense and
                advance.state == 'confirmed'):
            self.expense_line_ids.create({
                'name': _("Advance: ") + str(advance.name),
                'travel_id': travel.id,
                'expense_id': self.id,
                'line_type': "real_expense",
                'product_id': advance.product_id.id,
                'product_qty': 1.0,
                'unit_price': advance.amount,
                'control': True
            })
        if advance.state != 'cancel':
            advance.write({
                'state': 'closed',
                'expense_id': self.id
            })

    def create_fuel_line(self, fuel_log, travel):
        if (fuel_log.state not in ['confirmed', 'closed']):
            raise ValidationError(_(
                'Oops! All the voucher must be confirmed'
                '\n Name of voucher not confirmed: ' +
                fuel_log.name +
                '\n State: ' + fuel_log.state))
        for rec in self:
            if fuel_log.expense_line_id:
                fuel_expense = fuel_log.expense_line_id
            else:
                fuel_expense = rec.expense_line_ids.create({
                    'name': _(
                        "Fuel voucher: ") + str(fuel_log.name),
                    'travel_id': travel.id,
                    'expense_id': rec.id,
                    'line_type': 'fuel',
                    'product_id': fuel_log.product_id.id,
                    'product_qty': fuel_log.product_qty,
                    'product_uom_id': (
                        fuel_log.product_id.uom_id.id),
                    'unit_price': fuel_log.price_total,
                    'is_invoice': fuel_log.invoice_paid,
                    'invoice_id': fuel_log.invoice_id.id,
                    'control': True,
                    'partner_id': fuel_log.vendor_id.id or False,
                    'date': fuel_log.date,
                    'invoice_number': fuel_log.ticket_number,
                })
            if fuel_expense:
                fuel_log.write({
                    'state': 'closed',
                    'expense_id': rec.id
                })
        return fuel_expense

    def create_salary_line(self, travel):
        for rec in self:
            product_id = self.env['product.product'].search([
                ('tms_product_category', '=', 'salary')])
            if not product_id:
                raise ValidationError(_(
                    'Oops! You must create a product for the'
                    ' diver salary with the Salary TMS '
                    'Product Category'))
            if rec.employee_id.outsourcing is False:
                rec.expense_line_ids.create({
                    'name': _("Salary per travel: ") + str(travel.name),
                    'travel_id': travel.id,
                    'expense_id': rec.id,
                    'line_type': "salary",
                    'product_qty': 1.0,
                    'product_uom_id': product_id.uom_id.id,
                    'product_id': product_id.id,
                    'unit_price': rec.get_driver_salary(travel),
                    'control': True
                })

    def calculate_discounts(self, methods, loan):
        if loan.discount_type == 'fixed':
            total = loan.fixed_discount
        elif loan.discount_type == 'percent':
            total = loan.amount * (
                loan.percent_discount / 100)
        for key, value in methods.items():
            if loan.discount_method == key:
                if loan.expense_ids:
                    dates = []
                    for loan_date in loan.expense_ids:
                        dates.append(loan_date.date)
                    dates.sort(reverse=True)
                    end_date = datetime.strptime(
                        dates[0], "%Y-%m-%d")
                else:
                    end_date = datetime.strptime(
                        loan.date_confirmed, "%Y-%m-%d")
                start_date = datetime.strptime(
                    self.date, "%Y-%m-%d")
                total_date = start_date - end_date
                total_payment = total_date / value
                if int(total_payment.days) >= 1:
                    total_discount = (
                        total_payment.days * total)
            elif loan.discount_method == 'each':
                total_discount = total
        return total_discount

    def get_expense_loan(self):
        loans = self.env['tms.expense.loan'].search([
            ('employee_id', '=', self.employee_id.id),
            ('balance', '>', 0.0)])
        methods = {
            'monthly': 30,
            'fortnightly': 15,
            'weekly': 7,
        }
        for loan in loans:
            total_discount = 0.0
            payment = loan.payment_move_id.id
            ac_loan = loan.active_loan
            if not loan.lock and loan.state == 'confirmed' and payment:
                if ac_loan:
                    loan.write({
                        'expense_id': self.id
                    })
                    total_discount = self.calculate_discounts(methods, loan)
                    total_final = loan.balance - total_discount
                    if total_final <= 0.0:
                        total_discount = loan.balance
                        loan.write({'balance': 0.0, 'state': 'closed'})
                    expense_line = self.expense_line_ids.create({
                        'name': _("Loan: ") + str(loan.name),
                        'expense_id': self.id,
                        'line_type': "loan",
                        'product_id': loan.product_id.id,
                        'product_qty': 1.0,
                        'unit_price': total_discount,
                        'date': self.date,
                        'control': True
                    })
                    loan.expense_ids += expense_line
            elif loan.lock and loan.state == 'confirmed' and ac_loan:
                if loan.balance > 0.0:
                    loan.write({
                        'expense_id': self.id
                    })
                    expense_line = self.expense_line_ids.create({
                        'name': _("Loan: ") + str(loan.name),
                        'expense_id': self.id,
                        'line_type': "loan",
                        'product_id': loan.product_id.id,
                        'product_qty': 1.0,
                        'unit_price': loan.amount_discount,
                        'date': self.date,
                        'control': True
                    })
                loan.expense_ids += expense_line

    def get_travel_info(self):
        for rec in self:
            # Unattaching info from expense
            rec.unattach_info()
            # Finish unattach info from expense
            rec.get_expense_loan()
            for travel in rec.travel_ids:
                travel.write({'state': 'closed', 'expense_id': rec.id})
                for advance in travel.advance_ids:
                    # Creating advance lines
                    rec.create_advance_line(advance, travel)
                    # Finish creating advance lines
                for fuel_log in travel.fuel_log_ids:
                    # Creating fuel lines
                    rec.create_fuel_line(fuel_log, travel)
                    # Finish creating fuel lines
                # Creating salary lines
                rec.create_salary_line(travel)
                # Finish creating salary lines

    @api.depends('travel_ids')
    def get_driver_salary(self, travel):
        for rec in self:
            driver_salary = 0.0
            for waybill in travel.waybill_ids:
                income = 0.0
                for line in waybill.waybill_line_ids:
                    if line.product_id.apply_for_salary:
                        income += line.price_subtotal
                # TODO: define a new module to apply this functionality
                # if waybill.currency_id.name == 'USD':
                #     income = (income *
                #               self.env.user.company_id.expense_currency_rate)
                if waybill.driver_factor_ids:
                    for factor in waybill.driver_factor_ids:
                        driver_salary += factor.get_amount(
                            weight=waybill.product_weight,
                            distance=waybill.distance_route,
                            distance_real=waybill.distance_real,
                            qty=waybill.product_qty,
                            volume=waybill.product_volume,
                            income=income,
                            employee=rec.employee_id)
                elif travel.driver_factor_ids:
                    for factor in travel.driver_factor_ids:
                        driver_salary += factor.get_amount(
                            weight=waybill.product_weight,
                            distance=waybill.distance_route,
                            distance_real=waybill.distance_real,
                            qty=waybill.product_qty,
                            volume=waybill.product_volume,
                            income=income,
                            employee=rec.employee_id)
                else:
                    raise ValidationError(_(
                        'Oops! You have not defined a Driver factor in '
                        'the Travel or the Waybill\nTravel: %s') %
                        travel.name)
            return driver_salary

    def create_supplier_invoice(self, line):
        journal_id = self.operating_unit_id.expense_journal_id.id
        fpos = line.partner_id.property_account_position_id
        product_account = line.product_id.product_tmpl_id.get_product_accounts(
            fpos)['expense']
        if not product_account:
            raise ValidationError(
                _('Error !'),
                _('There is no expense account defined for this'
                    ' product: "%s") % (line.product_id.name'))
        if not journal_id:
            raise ValidationError(
                _('Error !',
                    'You have not defined Travel Expense Supplier Journal...'))
        invoice_line = (0, 0, {
            'name': _('%s (TMS Expense Record %s)') % (line.product_id.name,
                                                       line.expense_id.name),
            'account_id': product_account,
            'quantity': line.product_qty,
            'price_unit': line.unit_price,
            'tax_ids': [(6, 0, line.tax_ids.ids)],
            'product_uom_id': line.product_uom_id.id,
            'product_id': line.product_id.id,
        })
        notes = line.expense_id.name + ' - ' + line.product_id.name
        invoice = {
            'invoice_origin': line.expense_id.name,
            'type': 'in_invoice',
            'journal_id': journal_id,
            'ref': line.invoice_number,
            'partner_id': line.partner_id.id,
            'invoice_line_ids': [invoice_line],
            'currency_id': line.expense_id.currency_id.id,
            'invoice_payment_term_id': (
                line.partner_id.property_supplier_payment_term_id.id
                if
                line.partner_id.property_supplier_payment_term_id
                else False),
            'fiscal_position_id': (
                line.partner_id.property_account_position_id.id or False),
            'narration': notes,
            'operating_unit_id': line.expense_id.operating_unit_id.id,
        }
        invoice_id = self.env['account.move'].create(invoice)
        line.invoice_id = invoice_id
        return invoice_id

    def reconcile_supplier_invoices(self, invoice_ids, move_id):
        move_line_obj = self.env['account.move.line']
        for invoice in invoice_ids:
            moves = self.env['account.move.line']
            invoice_str_id = str(invoice.id)
            expense_move_line = move_line_obj.search(
                [('move_id', '=', move_id.id), (
                    'name', 'ilike', invoice_str_id)])
            if not expense_move_line:
                raise ValidationError(
                    _('Error ! Move line was not found,'
                        ' please check your data.'))
            moves |= expense_move_line
            moves |= invoice.line_ids.filtered(
                lambda x: x.account_id.reconcile and
                x.account_id.user_type_id.id in [2])
            moves.reconcile()
        return True

    @api.onchange('operating_unit_id', 'unit_id')
    def _onchange_operating_unit_id(self):
        travels = self.env['tms.travel'].search([
            ('operating_unit_id', '=', self.operating_unit_id.id),
            ('state', '=', 'done'),
            ('unit_id', '=', self.unit_id.id)])
        driver_ids = travels.mapped('employee_id').ids
        if self.employee_id.id not in driver_ids:
            self.employee_id = False
        tlines_units = self.travel_ids.mapped('unit_id').ids
        tlines_drivers = self.travel_ids.mapped('employee_id').ids
        if (self.unit_id.id not in tlines_units and
                self.employee_id.id not in tlines_drivers):
            self.travel_ids = False
        return {
            'domain': {
                'employee_id': [
                    ('id', 'in', driver_ids), ('driver', '=', True)],
            }
        }

    def get_amount_total(self):
        for rec in self:
            amount_subtotal = 0.0
            for line in rec.expense_line_ids:
                if line.line_type in ['real_expense', 'fuel', 'fuel_cash']:
                    amount_subtotal += line.price_subtotal
            return amount_subtotal

    def get_amount_tax(self):
        for rec in self:
            tax_amount = 0.0
            for line in rec.expense_line_ids:
                if line.line_type in ['real_expense', 'fuel', 'fuel_cash']:
                    tax_amount += line.tax_amount
            return tax_amount

    def get_value(self, type_line):
        for rec in self:
            value = 0.0
            for line in rec.expense_line_ids:
                if line.line_type == type_line:
                    value += line.price_total
        return value
