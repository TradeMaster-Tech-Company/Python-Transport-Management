# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import os
from datetime import datetime

import pytz
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TmsTollImport(models.TransientModel):
    _name = 'tms.toll.import'

    filename = fields.Char(size=255)
    file = fields.Binary(
        string='Upload the data',
        required=True)

    @api.multi
    def update_tollstation_expense(self):
        txt_extension = os.path.splitext(self.filename)[1].lower()
        if txt_extension == '.txt' or txt_extension == '.dat':
            try:
                document = base64.b64decode(self.file)
                lines = document.split('\n')
                lines.remove('')
                for line in lines:
                    if (line == '\r' or
                            line[:10] == 'Tag,No.Eco'):
                        continue
                    split_line = line.split('|')
                    flag = split_line[0].split('\t')
                    if len(flag) == 2:
                        split_line[0] = flag[1]
                    if split_line[5][-1] == '.':
                        split_line[5].replace('.', '')
                    toll_datetime = str(split_line[2] + ' ' + split_line[3])
                    if toll_datetime == 'Fecha de Trans. Caseta':
                        continue
                    try:
                        create_date = datetime.strptime(
                            toll_datetime, "%Y/%m/%d %H:%M:%S")
                    except ValueError:
                        create_date = datetime.strptime(
                            toll_datetime, "%d/%m/%Y %H:%M:%S")
                    local_tz = pytz.timezone(self._context['tz'])
                    datetime_with_tz = local_tz.localize(
                        create_date, is_dst=None)
                    txt_date = fields.Datetime.to_string(
                        datetime_with_tz.astimezone(pytz.utc))
                    num_tag = split_line[0].replace('.', '')
                    amount_total = (
                        split_line[5].replace('$', '').replace(' ', ''))
                    exists = self.env['tms.toll.data'].search([
                        ('date', '=', txt_date),
                        ('num_tag', '=', num_tag)])
                    if not exists:
                        self.env['tms.toll.data'].create({
                            'name': split_line[4],
                            'num_tag': num_tag,
                            'economic_number': split_line[1],
                            'date': txt_date,
                            'import_rate': amount_total,
                            })
            except Exception as message:
                raise ValidationError(_(
                    'Oops! Odoo has detected an error'
                    ' in the file. \nPlease contact your admin system.\n\n'
                    'Error message\n[' + str(message) + ']'))
        else:
            raise ValidationError(
                _('Oops! The files must have .txt or .dat extensions'))
        return {
            'name': 'Toll station data',
            'view_mode': 'tree',
            'target': 'current',
            'res_model': 'tms.toll.data',
            'type': 'ir.actions.act_window',
        }
