# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError


class TmsExpenseLoan(models.Model):
    _name = "tms.expense.loan"
    _inherit = 'mail.thread'
    _description = "Tms Expense Loan"

    operating_unit_id = fields.Many2one(
        'operating.unit', string='Operating Unit', required=True)
    name = fields.Char()
    date = fields.Date(
        required=True,
        default=fields.Date.context_today
    )
    date_confirmed = fields.Date(
        readonly=True,
        related='move_id.date',
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Driver',
        required=True,
    )
    expense_ids = fields.Many2many(
        'tms.expense.line', readonly=True
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('authorized', 'Waiting for authorization'),
            ('approved', 'Approved'),
            ('confirmed', 'Confirmed'),
            ('closed', 'Closed'),
            ('cancel', 'Cancelled'),
        ],
        tracking=True,
        readonly=True,
        default='draft',
    )
    discount_method = fields.Selection(
        selection=[
            ('each', 'Each Travel Expense Record'),
            ('weekly', 'Weekly'),
            ('fortnightly', 'Fortnightly'),
            ('monthly', 'Monthly'),
        ],
        required=True,
    )
    discount_type = fields.Selection(
        selection=[
            ('fixed', 'Fixed'),
            ('percent', 'Loan Percentage'),
        ],
        required=True,
    )
    notes = fields.Text()
    origin = fields.Char()
    amount = fields.Float(required=True)
    percent_discount = fields.Float()
    fixed_discount = fields.Float()
    paid = fields.Boolean(
        compute='_compute_paid',
        store=True, readonly=True)
    balance = fields.Float(compute='_compute_balance', store=True)
    active_loan = fields.Boolean()
    lock = fields.Boolean(string='Other discount?')
    amount_discount = fields.Float()
    product_id = fields.Many2one(
        'product.product', 'Discount Product',
        required=True,
        domain=[('tms_product_category', '=', 'loan')])
    expense_id = fields.Many2one(
        'tms.expense', 'Expense Record', readonly=True)
    payment_move_id = fields.Many2one(
        'account.move',
        string="Payment Entry",
        readonly=True,
        ondelete='restrict',)
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    move_id = fields.Many2one(
        'account.move', 'Journal Entry',
        help="Link to the automatically generated Journal Items.\nThis move "
        "is only for Loan Expense Records with balance < 0.0",
        readonly=True,
        ondelete='restrict',)
    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, values):
        loan = super().create(values)
        if not loan.operating_unit_id.loan_sequence_id:
            raise ValidationError(_(
                'You need to define the sequence for loans in base %s') %
                loan.operating_unit_id.name)
        sequence = loan.operating_unit_id.loan_sequence_id
        loan.name = sequence.next_by_id()
        return loan

    def action_authorized(self):
        for rec in self:
            rec.state = 'approved'

    def action_approve(self):
        for rec in self:
            if rec.discount_type == 'fixed' and rec.fixed_discount <= 0.0:
                raise exceptions.ValidationError(
                    _('Could not approve the Loan.'
                      ' The Amount of discount must be greater than zero.'))
            if (rec.discount_type == 'percent' and rec.percent_discount <= 0.0):  # noqa
                raise exceptions.ValidationError(
                    _('Could not approve the Loan.'
                      ' The Amount of discount must be greater than zero.'))

            rec.state = 'approved'

    def action_cancel(self):
        for rec in self:
            if rec.paid:
                payment_move_id = rec.payment_move_id
                rec.payment_move_id = False
                payment_move_id.button_cancel()
                payment_move_id.line_ids.remove_move_reconcile()

            move_id = rec.move_id
            rec.move_id = False
            if move_id.state == 'posted':
                move_id.button_cancel()
            rec.state = 'cancel'

    def action_confirm(self):
        for loan in self:
            obj_account_move = self.env['account.move']
            loan_journal_id = (
                loan.operating_unit_id.loan_journal_id.id)
            loan_debit_account_id = (
                loan.employee_id.
                tms_loan_account_id.id
            )
            loan_credit_account_id = (
                loan.employee_id.
                address_home_id.property_account_payable_id.id
            )
            if not loan_journal_id:
                raise exceptions.ValidationError(
                    _('Warning! The loan does not have a journal'
                      ' assigned. Check if you already set the '
                      'journal for loans in the base.'))
            if not loan_credit_account_id:
                raise exceptions.ValidationError(
                    _('Warning! The driver does not have a home address'
                      ' assigned. Check if you already set the '
                      'home address for the employee.'))
            if not loan_debit_account_id:
                raise exceptions.ValidationError(
                    _('Warning! You must have configured the accounts '
                      'of the tms'))
            move_lines = []
            notes = _('* Base: %s \n'
                      '* Loan: %s \n'
                      '* Driver: %s \n') % (
                          loan.operating_unit_id.name,
                          loan.name,
                          loan.employee_id.name)
            total = loan.currency_id._convert(
                loan.amount, self.env.user.currency_id, loan.company_id,
                loan.date)
            if total > 0.0:
                accounts = {'credit': loan_credit_account_id,
                            'debit': loan_debit_account_id}
                for name, account in accounts.items():
                    move_line = (0, 0, {
                        'name': loan.name,
                        'partner_id': (
                            loan.employee_id.address_home_id.id),
                        'account_id': account,
                        'debit': (total if name == 'debit' else 0.0),
                        'credit': (total if name == 'credit' else 0.0),
                        'journal_id': loan_journal_id,
                        'operating_unit_id': loan.operating_unit_id.id,
                    })
                    move_lines.append(move_line)
                move = {
                    'date': fields.Date.today(),
                    'journal_id': loan_journal_id,
                    'name': _('Loan: %s') % (loan.name),
                    'line_ids': move_lines,
                    'operating_unit_id': loan.operating_unit_id.id,
                    'narration': notes,
                }
                move_id = obj_account_move.create(move)
                move_id.action_post()
                self.write(
                    {
                        'move_id': move_id.id,
                        'state': 'confirmed',
                    })

    def action_cancel_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('expense_ids')
    def _compute_balance(self):
        for loan in self:
            line_amount = 0.0
            if not loan.expense_ids:
                loan.balance = loan.amount
            else:
                for line in loan.expense_ids:
                    line_amount += line.price_total
                loan.balance = loan.amount + line_amount
            if loan.balance <= 0.0:
                loan.write({'state': 'closed'})

    def unlink(self):
        for rec in self:
            if rec.state == 'confirmed' or rec.state == 'closed':
                raise ValidationError(
                    _('You can not delete a Loan'
                      ' in status confirmed or closed'))
            return super().unlink()

    @api.depends('payment_move_id')
    def _compute_paid(self):
        for rec in self:
            rec.paid = False
            if rec.payment_move_id.id:
                rec.paid = True

    def action_pay(self):
        for rec in self:
            bank = self.env['account.journal'].search(
                [('type', '=', 'bank')])[0]
            wiz = self.env['tms.wizard.payment'].with_context(
                active_model='tms.expense.loan', active_ids=[rec.id]).create({
                    'journal_id': bank.id,
                    'amount_total': rec.amount,
                    'date': rec.date,
                })
            wiz.make_payment()
