# coding: utf-8
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging
from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def execute_create_ir_attachment(cr):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        _logger.info('Create attachment')
        att_obj = env['ir.attachment']
        cr.execute(str(
            """SELECT id, pdf_filename, pdf_file, xml_filename, xml_file
               FROM tms_expense_line
               WHERE xml_file is not NULL AND pdf_file is not NULL;
            """))
        expense_line_ids = cr.fetchall()
        list_expense_line_ids = []
        for expense in expense_line_ids:
            list_expense_line_ids.append(expense[0])
            att_obj.create({
                'name': expense[3],
                'datas': expense[4],
                'datas_fname': expense[3],
                'res_model': 'tms.expense.line',
                'res_id': expense[0],
                'res_field': 'xml_file',
            })
            att_obj.create({
                'name': expense[1],
                'datas': expense[2],
                'datas_fname': expense[1],
                'res_model': 'tms.expense.line',
                'res_id': expense[0],
                'res_field': 'pdf_file',
            })
        cr.execute(str(
            """UPDATE tms_expense_line
               SET pdf_file = NULL,
                   xml_file = NULL
               WHERE id IN  %s """) % (tuple(list_expense_line_ids),))
        cr.commit()


def migrate(cr, version):
    execute_create_ir_attachment(cr)
