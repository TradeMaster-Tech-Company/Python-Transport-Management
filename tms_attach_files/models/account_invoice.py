# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from codecs import BOM_UTF8
from lxml import objectify
from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare
BOM_UTF8U = BOM_UTF8.decode('UTF-8')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _validate_xml(self, xml_signed):
        try:
            expense_line = self.env['tms.expense.line'].search(
                [('invoice_id', '=', self.id)])
            xml_str = base64.decodestring(xml_signed).lstrip(BOM_UTF8)
            xml_str_rep = xml_str.replace(
                'xmlns:schemaLocation', 'xsi:schemaLocation')
            xml = objectify.fromstring(xml_str_rep)
            xml_vat_emitter = xml.Emisor.get(
                'rfc', xml.Emisor.get('Rfc', ''))
            xml_vat_receiver = xml.Receptor.get(
                'rfc', xml.Receptor.get('Rfc', ''))
            xml_amount = xml.get(
                'total', xml.get('Total', ''))
            xml_uuid = self.l10n_mx_edi_get_tfd_etree(xml)
        except AttributeError as ex:
            raise ValidationError(ex)
        except SyntaxError as ex:
            raise ValidationError(
                _('Error in XML structure\n%s \n %s') %
                str(ex), expense_line.name)
        validate_xml = False
        try:
            validate_xml = self._validate_xml_sat(
                xml_vat_emitter, xml_vat_receiver, xml_amount, xml_uuid)
        except ValidationError:
            self.message_post(_(
                'Cannot be verified the SAT status for this document, please '
                'verify that the CFDI is valid before validate this record.'))
        if validate_xml and validate_xml.Estado == 'Cancelado':
            raise ValidationError(
                _('This XML state is CANCELED in the SAT system.\n' +
                  'Expense line: ' + expense_line.name + '\nTravel: ' +
                  expense_line.travel_id.name))
        if xml_uuid:
            xml_exists = self.search([('cfdi_uuid', '=', xml_uuid)])
            if xml_exists:
                raise ValidationError(_(
                    'Can not attach this XML because other invoice already '
                    'have the same UUID that this XML. \n Invoice: %s'
                    '\n Line: %s') % (
                    xml_exists.number, expense_line.name))
        inv_vat_receiver = self.company_id.address_parent_company_id.vat
        inv_vat_emitter = self.commercial_partner_id.vat
        inv_amount = self.amount_total or 0.0
        msg = ''
        if not inv_vat_emitter:
            msg = (_("This supplier does not have VAT configured."
                     "\n Supplier: %s \n Line: %s ") %
                   (expense_line.partner_id.name, expense_line.name))
        elif not inv_vat_receiver:
            msg = _("Please check that your company have a VAT configured.")
        elif inv_vat_receiver.upper() != xml_vat_receiver.upper():
            msg = (_('The VAT receiver do not match with the Company.'
                     '\n Company VAT: %s \n XML File: %s'
                     '\n Expense Line: %s') %
                   (inv_vat_receiver.upper(), xml_vat_receiver.upper(),
                    expense_line.name))
        elif inv_vat_emitter.upper() != xml_vat_emitter.upper():
            msg = (_(
                'The VAT emitter do not match with the supplier invoice.'
                '\n Supplier VAT: %s \n XML File: %s'
                '\n Expense Line: %s ') % (
                    inv_vat_emitter.upper(), xml_vat_emitter.upper(),
                    expense_line.name))
        # Use 2 as precision rounding by the decimals in XML
        elif float_compare(
                float(inv_amount), float(xml_amount), precision_rounding=6):
            msg = (_(
                "The invoice total not match with the XML file."
                "\n Amount Total Invoice: %s \n XML File: %s"
                "\n Expense Line: %s") % (
                    inv_amount, xml_amount, expense_line.name))
        if msg:
            raise ValidationError(msg)
        self.write({
            'cfdi_uuid': xml_uuid,
            'xml_signed': base64.decodestring(xml_signed)})
        name = expense_line.xml_filename
        if not self.xml_signed:
            return False
        data_attach = {
            'name': name,
            'datas': base64.encodestring(
                self.xml_signed and
                self.xml_signed.lstrip(BOM_UTF8U).encode('UTF-8') or ''),
            'datas_fname': name,
            'description': _('XML signed from Invoice %s.' % self.number),
            'res_model': self._name,
            'res_id': self.id,
        }
        self.env['ir.attachment'].with_context({}).create(data_attach)
        return True

    @api.multi
    def _validate_invoice_xml(self, xml_signed):
        xml_str = base64.decodestring(xml_signed).lstrip(BOM_UTF8)
        xml_str_rep = xml_str.replace(
            'xmlns:schemaLocation', 'xsi:schemaLocation')
        xml_64 = base64.encodestring(xml_str_rep).lstrip(BOM_UTF8)
        res = super()._validate_invoice_xml(xml_64)
        return res
