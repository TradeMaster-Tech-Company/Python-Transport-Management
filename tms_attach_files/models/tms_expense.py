# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class TmsExpense(models.Model):
    _inherit = 'tms.expense'

    @api.multi
    def create_supplier_invoice(self, lines):
        for line in lines:
            res = super().create_supplier_invoice(line)
            if line.is_invoice:
                vals = {
                    'file_xml_sign': line.xml_file,
                    'file_pdf': line.pdf_file,
                    'xml_name': line.xml_filename,
                    'pdf_name': line.pdf_filename,
                }
                wiz = self.env['tms.attachment.wizard'].with_context(
                    active_id=res.id).create(vals)
                wiz.attach_files()
            return res
