# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class TmsExpense(models.Model):
    _inherit = 'tms.expense'

    @api.multi
    def get_retention(self):
        for rec in self:
            retentions = self.env['tms.retention'].search([])
            for retention in retentions:
                value = 0.0
                if (retention.employee_ids and rec.employee_id not in
                        retention.employee_ids):
                    continue
                if retention.type == 'days':
                    if not rec.start_date and not rec.end_date:
                        raise ValidationError(
                            _('You need to set travel duration'))
                    days = int(rec.travel_days.split('D')[0]) or 0
                    value += retention.factor * days
                else:
                    value += retention.factor * rec.amount_salary
                if retention.mixed:
                    value += retention.fixed_amount
                rec.expense_line_ids.create({
                    'name': retention.name,
                    'expense_id': rec.id,
                    'line_type': "salary_retention",
                    'product_qty': 1.0,
                    'product_uom_id': retention.product_id.uom_id.id,
                    'product_id': retention.product_id.id,
                    'unit_price': value,
                    'control': True
                })

    @api.multi
    def get_travel_info(self):
        for rec in self:
            res = super().get_travel_info()
            rec.get_retention()
            return res
