# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TmsTollData(models.Model):
    _name = 'tms.toll.data'
    _order = 'date asc'
    date = fields.Datetime()
    name = fields.Char()
    num_tag = fields.Char(string='Tag number')
    economic_number = fields.Char()
    import_rate = fields.Float()
    expense_line_id = fields.Many2one(
        'tms.expense.line', string='Expense line')
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed')],
        default='open')
