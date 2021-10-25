# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, models


class TmsWizardInvoice(models.TransientModel):
    _name = 'tms.wizard.invoice'
    _description = 'Wizard to create invoices from Waybills'

    @api.model
    def prepare_lines(self, product, quantity,
                      price_unit, tax, account, origin):
        return {
            'product_id': product.id,
            'quantity': quantity,
            'price_unit': price_unit,
            'product_uom_id': product.uom_id.id,
            'tax_ids': [(6, 0, tax.ids)],
            'name': product.display_name + '\n' + origin,
            'account_id': account.id,
        }

    @api.model
    def compute_waybill(self, record, lines):
        res = {}
        res['invoice_type'] = 'out_invoice'
        res['operating_unit_id'] = record.operating_unit_id
        partner_id = record.partner_invoice_id
        res['partner_id'] = partner_id
        fpos = partner_id.property_account_position_id
        res['fpos'] = fpos
        res['invoice_account'] = fpos.map_account(
            partner_id.property_account_receivable_id)
        for line in record.waybill_line_ids:
            if line.product_id.property_account_income_id:
                account = fpos.map_account(
                    line.product_id.property_account_income_id)
            elif (line.product_id.categ_id.
                    property_account_income_categ_id):
                account = fpos.map_account(
                    line.product_id.categ_id.
                    property_account_income_categ_id)
            else:
                raise exceptions.ValidationError(
                    _('You must have an income account in the '
                      'product or its category.'))
            tax = fpos.map_tax(
                line.tax_ids)
            if line.price_subtotal > 0.0:
                lines.append(
                    (0, 0, self.prepare_lines
                        (line.product_id, line.product_qty,
                         line.price_subtotal, tax, account, record.name)))
        res['lines'] = lines
        return res

    @api.model
    def compute_fuel_log(self, record, lines):
        res = {}
        res['invoice_type'] = 'in_invoice'
        res['operating_unit_id'] = record.operating_unit_id
        partner_id = record.vendor_id
        res['partner_id'] = partner_id
        fpos = partner_id.property_account_position_id
        res['fpos'] = fpos
        res['invoice_account'] = fpos.map_account(
            partner_id.property_account_payable_id)
        ieps = record.operating_unit_id.ieps_product_id
        products = [record.product_id, ieps]
        for product in products:
            account = product.product_tmpl_id.get_product_accounts(fpos).get(
                'expense', False)
            if not account:
                raise exceptions.ValidationError(
                    _('You must have an expense account in the '
                      'product or its category'))
            tax = fpos.map_tax(product.supplier_taxes_id)
            if product.id == record.product_id.id:
                lines.append(
                    (0, 0, self.prepare_lines
                        (product, record.product_qty,
                         record.price_unit, tax, account, record.name)))
            elif product.id == ieps.id:
                lines.append(
                    (0, 0, self.prepare_lines
                        (record.operating_unit_id.ieps_product_id, 1.0,
                         record.special_tax_amount, tax,
                         account, record.name)))
        res['lines'] = lines
        return res

    def make_invoices(self):
        record_names = []
        currency_ids = []
        partner_ids = []
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        for record in records:
            if record.invoice_id:
                raise exceptions.ValidationError(
                    _('The record is already invoiced'))
            if record.state not in ['confirmed', 'closed']:
                raise exceptions.ValidationError(
                    _('The record must be confirmed or closed'))
            record_names.append(record.name)
            currency_ids.append(record.currency_id.id)
            currency_id = record.currency_id.id
            journal_id = record.operating_unit_id.sale_journal_id.id
            if active_model == 'tms.waybill':
                res = self.compute_waybill(record, lines)
            elif active_model == 'fleet.vehicle.log.fuel':
                journal_id = record.operating_unit_id.purchase_journal_id.id
                res = self.compute_fuel_log(record, lines)
            partner_ids.append(res['partner_id'].id)

        if len(set(partner_ids)) > 1:
            raise exceptions.ValidationError(
                _('The records must be of the same partner.'))
        if len(set(currency_ids)) > 1:
            raise exceptions.ValidationError(
                _('The records must be of the same currency.'))
        invoice_id = self.env['account.move'].create({
            'partner_id': res['partner_id'].id,
            'operating_unit_id': res['operating_unit_id'].id,
            'fiscal_position_id': res['fpos'].id,
            'journal_id': journal_id,
            'currency_id': currency_id,
            'move_type': res['invoice_type'],
            'invoice_line_ids': res['lines'],
        })
        records.write({'invoice_id': invoice_id.id})
        message = _(
            '<strong>Invoice of:</strong> %s </br>') % (
            ', '.join(record_names))
        invoice_id.message_post(body=message)
        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'account.move',
            'res_id': invoice_id.id,
            'type': 'ir.actions.act_window'
        }
