# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import api, fields, models


class TmsExpenseLine(models.Model):
    _inherit = 'tms.expense.line'

    tollstation_ids = fields.Many2many(
        'tms.toll.data', string='Tollstations')
    tollstation_tag = fields.Char()

    @api.onchange('tollstation_ids')
    def _onchange_tollstation(self):
        for rec in self:
            total = 0
            for toll in rec.tollstation_ids:
                total += toll.import_rate / 1.16
                toll.write({'expense_id': rec.expense_id.id})
            rec.price_subtotal = total
            rec.unit_price = total

    @api.onchange('expense_id')
    def _onchange_iave_tolls(self):
        for rec in self:
            rec.tollstation_tag = rec.expense_id.unit_id.tollstation_tag

    @api.model
    def create(self, values):
        res = super().create(values)
        res.tollstation_ids.write({
            'state': 'closed',
            'expense_line_id': res.id})
        return res

    @api.multi
    def write(self, values):
        for rec in self:
            res = super().write(values)
            tolls = self.env['tms.toll.data'].search(
                [('expense_line_id', '=', self.id)])
            tolls.write({
                'expense_line_id': False,
                'state': 'closed'})
            for toll in rec.tollstation_ids:
                toll.write({
                    'state': 'closed',
                    'expense_line_id': rec.id})
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            tolls = self.env['tms.toll.data'].search(
                [('expense_line_id', '=', rec.id)])
            tolls.write({
                'state': 'open',
                'expense_line_id': False})
        return super().unlink()

    @api.multi
    def sort_expense_lines(self):
        for rec in self:
            ordered_lines = sorted(
                rec.tollstation_ids,
                key=lambda x: datetime.strptime(
                    x['date'], '%Y-%m-%d %H:%M:%S'))
            return ordered_lines
