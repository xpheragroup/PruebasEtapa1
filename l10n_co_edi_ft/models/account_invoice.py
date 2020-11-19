# No member error in this file are for inheritance in Odoo!
# pylint: disable=E1101

# coding: utf-8
import pytz
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools.float_utils import float_compare
from .facturatech_request import FacturatechRequest, FacturatechException

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _l10n_co_edi_create_ft_request(self):
        company = self.company_id
        return FacturatechRequest(company.l10n_co_edi_username, company.l10n_co_edi_password, company.l10n_co_edi_test_mode)

    def l10n_co_edi_upload_electronic_invoice(self):
        '''Main function that prepares the XML, uploads it to Carvajal and
        deals with the output. This output is posted as chatter
        messages.
        '''
        for invoice in self:
            try:
                request = self._l10n_co_edi_create_carvajal_request()
                xml_filename = invoice._l10n_co_edi_generate_electronic_invoice_filename()
                xml = invoice.l10n_co_edi_generate_electronic_invoice_xml()
                print(xml)
                response = request.upload(xml_filename, xml)
            except FacturatechException as e:
                invoice.message_post(body=_('Carga de la factura electrónica falló. Mensaje de FacturaTech:<br/>%s') % e,
                                     attachments=[(xml_filename, xml)])
            except requests.HTTPError as e:
                if e.response.status_code == 503:
                    raise UserError(_("Carga de la factura electrónica falló. Probablemente el servicio no está disponible."))
                raise UserError(e)
            else:
                invoice.message_post(body=_('Cargue de factura electrónica exitosa. Mensaje de Facturatech:<br/>%s') % response['message'],
                                     attachments=[(xml_filename, xml)])
                invoice.l10n_co_edi_transaction = response['transactionId']
                invoice.l10n_co_edi_invoice_status = 'processing'

    def l10n_co_edi_download_electronic_invoice(self):
        '''Downloads a ZIP containing an official XML and signed PDF
        document. This will only be available for invoices that have
        been successfully validated by Facturatech and the government.
        '''
        ft_type = False
        if self.type == 'out_refund':
            ft_type = 'NC'
        elif self.type == 'in_refund':
            ft_type = 'ND'
        else:
            odoo_type_to_ft_type = {
                '1': 'FV',
                '2': 'FE',
                '3': 'FC',
            }
            ft_type = odoo_type_to_ft_type[self.l10n_co_edi_type]

        request = self._l10n_co_edi_create_ft_request()
        try:
            response = request.download(self.journal_id.sequence_id.prefix, self.name, ft_type)
        except FacturatechException as e:
            return _('Descarga de factura electrónica fallida. Mensaje de Facturatech:<br/>%s') % e, []
        else:
            return _('Descarga de factura electrónica exitosa. Mensaje de Facturatech:<br/>%s') % response['message'], [('%s.zip' % self.name, response['zip_b64'])]

    def l10n_co_edi_check_status_electronic_invoice(self):
        '''This checks the current status of an uploaded XML with Facturatech. It
        posts the results in the invoice chatter and also attempts to
        download a ZIP containing the official XML and PDF if the
        invoice is reported as fully validated.
        '''
        for invoice in self.filtered('l10n_co_edi_transaction'):
            request = invoice._l10n_co_edi_create_carvajal_request()
            try:
                response = request.check_status(invoice.l10n_co_edi_transaction)
            except FacturatechException as e:
                invoice.message_post(body=_('Revisión del estado de la factura en Facturatech falló. Mensaje de Facturatech:<br/>%s') % e)
            else:
                if response['status'] == 'PROCESSING':
                    invoice.l10n_co_edi_invoice_status = 'processing'
                else:
                    invoice.l10n_co_edi_invoice_status = 'accepted' if response['legalStatus'] == 'ACCEPTED' else 'rejected'

                msg = _('Revisión del estado de la factura en Facturatech exitoso. Mensaje de Facturatech:<br/>Estado: %s') % response['status']
                attachments = []

                if response['errorMessage']:
                    msg += _('<br/>Mensaje de error: %s') % response['errorMessage'].replace('\n', '<br/>')
                if response['legalStatus']:
                    msg += _('<br/>Estado legal: %s') % response['legalStatus']
                if response['governmentResponseDescription']:
                    msg += _('<br/>Respuesta guvernamental: %s') % response['governmentResponseDescription']

                if invoice.l10n_co_edi_invoice_status == 'accepted':
                    invoice_download_msg, attachments = invoice.l10n_co_edi_download_electronic_invoice()
                    msg += '<br/><br/>' + invoice_download_msg

                invoice.message_post(body=msg, attachments=attachments)

    def _l10n_co_edi_generate_xml(self):
        '''Renders the XML that will be sent to Carvajal.'''
        # generate xml with strings in language of customer
        self = self.with_context(lang=self.partner_id.lang)

        imp_taxes = self.env.ref('l10n_co_edi.tax_type_0') |\
            self.env.ref('l10n_co_edi.tax_type_1') |\
            self.env.ref('l10n_co_edi.tax_type_2') |\
            self.env.ref('l10n_co_edi.tax_type_3') |\
            self.env.ref('l10n_co_edi.tax_type_4')
        tax_lines_with_type = self.line_ids.filtered(lambda line: line.tax_line_id).filtered(lambda tax: tax.tax_line_id.l10n_co_edi_type in imp_taxes)
        retention_taxes = tax_lines_with_type.filtered(lambda tax: tax.tax_line_id.l10n_co_edi_type.retention)
        regular_taxes = tax_lines_with_type - retention_taxes
        ovt_tax_codes = ('01C', '02C', '03C')
        ovt_taxes = self.line_ids.filtered(lambda line: line.tax_line_id).filtered(lambda tax: tax.tax_line_id.l10n_co_edi_type.code in ovt_tax_codes)
        invoice_type_to_ref_1 = {
            'out_invoice': 'IV',
            'in_invoice': 'IV',
            'out_refund': 'NC',
            'in_refund': 'ND',
        }

        return self.env.ref('l10n_co_edi.electronic_invoice_xml').render({
            'invoice': self,
            'company_partner': self.company_id.partner_id,
            'sales_partner': self.invoice_user_id,
            'invoice_partner': self.partner_id.commercial_partner_id,
            'retention_taxes': retention_taxes,
            'regular_taxes': regular_taxes,
            'shipping_partner': self.env['res.partner'].browse(self._get_invoice_delivery_partner_id()),
            'invoice_type_to_ref_1': invoice_type_to_ref_1,
            'ovt_taxes': ovt_taxes,
            'float_compare': float_compare,
            'notas': self._l10n_co_edi_get_notas(),
        })