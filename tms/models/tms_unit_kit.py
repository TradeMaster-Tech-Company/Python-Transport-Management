# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class TmsUnitKit(models.Model):
    _name = "tms.unit.kit"
    _inherit = 'mail.thread'
    _order = "unit_id desc"
    _description = "Units Kits"

    name = fields.Char(required=True)
    unit_id = fields.Many2one('fleet.vehicle', 'Unit', required=True)
    trailer1_id = fields.Many2one('fleet.vehicle', 'Trailer 1')
    dolly_id = fields.Many2one('fleet.vehicle', 'Dolly')
    trailer2_id = fields.Many2one('fleet.vehicle', 'Trailer 2')
    employee_id = fields.Many2one(
        'hr.employee', 'Driver', domain=[('driver', '=', True)])
    date_start = fields.Datetime()
    date_end = fields.Datetime()
    notes = fields.Text()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(unit_id,name)',
         'Kit name number must be unique for each unit !'),
    ]
