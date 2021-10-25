# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TmsTollData(models.Model):
    _name = 'tms.toll.data'
    _description = 'Toll Data'

    date = fields.Datetime()
    num_tag = fields.Char(string='Tag number')
    economic_number = fields.Char()
    toll_station = fields.Char()
    import_rate = fields.Float()
