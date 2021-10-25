# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class OperatingUnit(models.Model):
    _inherit = 'operating.unit'

    travel_sequence_id = fields.Many2one(
        'ir.sequence', string='Travel Sequence')
    prepaid_fuel_sequence_id = fields.Many2one(
        'ir.sequence', string='Prepaid Sequence',)
    fuel_log_sequence_id = fields.Many2one(
        'ir.sequence', string='Fuel Log Sequence')
    advance_sequence_id = fields.Many2one(
        'ir.sequence', string='Advance Sequence')
    waybill_sequence_id = fields.Many2one(
        'ir.sequence', string='Waybill Sequence')
    expense_sequence_id = fields.Many2one(
        'ir.sequence', string='Expense Sequence')
    loan_sequence_id = fields.Many2one(
        'ir.sequence', string='Expense Loan Sequence')
    advance_journal_id = fields.Many2one(
        'account.journal', string='Advance Journal')
    expense_journal_id = fields.Many2one(
        'account.journal', string='Expense Journal')
    loan_journal_id = fields.Many2one(
        'account.journal', string='Expense Loan Journal')
    sale_journal_id = fields.Many2one(
        'account.journal', string='Sale Journal')
    purchase_journal_id = fields.Many2one(
        'account.journal', string='Purchase Journal')
    ieps_product_id = fields.Many2one(
        'product.product', string='IEPS Product')
    credit_limit = fields.Float()
