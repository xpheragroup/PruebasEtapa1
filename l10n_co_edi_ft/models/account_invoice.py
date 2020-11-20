# No member error in this file are for inheritance in Odoo!
# pylint: disable=E1101

# coding: utf-8
import pytz
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools.float_utils import float_compare
from .facturatech_request import FacturatechRequest, FacturatechZeepException, FacturatechWSException

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_co_edi_invoice_prefix = fields.Char('Electronic Prefix', help='The prefix to be sent to FT.', readonly=True, copy=False)
    l10n_co_edi_invoice_folio = fields.Char('Electronic Folio', help='The folio to be sent to FT.', readonly=True, copy=False)

    @api.model
    def _l10n_co_edi_create_ft_request(self):
        company = self.company_id
        return FacturatechRequest(company.l10n_co_edi_username, company.l10n_co_edi_password, company.l10n_co_edi_test_mode)

    def _l10n_co_edi_get_electronic_invoice_prefix(self):
        INVOICE_TYPE_TO_ENC_1 = {
            'out_invoice': 'TCFA',
            'in_invoice': 'TCFA',
            'out_refund': 'TCNC',
            'in_refund': 'TCND',
        }

        return INVOICE_TYPE_TO_ENC_1[self.type]

    def l10n_co_edi_upload_electronic_invoice_original_edi(self):
        '''Main function that prepares the XML, uploads it to Carvajal and
        deals with the output. This output is posted as chatter
        messages.
        '''
        for invoice in self:
            try:
                request = self._l10n_co_edi_create_ft_request()
                xml_filename = invoice._l10n_co_edi_generate_electronic_invoice_filename()
                xml = invoice.l10n_co_edi_generate_electronic_invoice_xml()
                print(xml.decode('utf-8'))
                response = request.upload(xml_filename, xml)
            except FacturatechWSException as e:
                raise Warning(e)
            except FacturatechZeepException as e:
                invoice.message_post(body=_('Carga de la factura electrónica falló. Mensaje de FacturaTech:<br/>%s') % e,
                                     attachments=[(xml_filename, xml)])
                return
            except requests.HTTPError as e:
                if e.response.status_code == 503:
                    raise UserError(_("Carga de la factura electrónica falló. Probablemente el servicio no está disponible."))
                raise UserError(e)
            invoice.message_post(body=_('Cargue de factura electrónica exitosa. Mensaje de Facturatech:<br/>%s') % response['message'],
                                    attachments=[(xml_filename, xml)])
            invoice.l10n_co_edi_transaction = response['transactionId']
            invoice.l10n_co_edi_invoice_status = 'processing'

    def l10n_co_edi_upload_electronic_invoice(self):
        """Some checks already before sending the electronic invoice to Facturatech"""
        to_process = self.filtered(lambda move: move._l10n_co_edi_is_l10n_co_edi_required())
        if to_process:
            if to_process.filtered(lambda m: not m.partner_id.vat):
                raise UserError(_('No puedes validar una factura que tiene un cliente/proveedor sin número de NIT.'))
            if to_process.filtered(lambda m: not m.partner_id.l10n_co_edi_obligation_type_ids):
                raise UserError(_('Toda la inforamción en los campos de la sección "Información Tributaria" del cliente deben ser establecidos.'))
            for inv in to_process:
                if (inv.l10n_co_edi_type == '2' and any(l.product_id and not l.product_id.l10n_co_edi_customs_code for l in inv.invoice_line_ids)) or (
                    any(l.product_id and not l.product_id.default_code and not l.product_id.barcode and not l.product_id.unspsc_code_id for l in inv.invoice_line_ids)):
                    raise UserError(_('Todo producto en las líneas de factura deben tener establecidos por lo menos un código de producto (código de barras, unspsc, código interno). '))
            to_process.write({'l10n_co_edi_datetime_invoice': fields.Datetime.now()})
        return self.l10n_co_edi_upload_electronic_invoice_original_edi()


    def l10n_co_edi_download_electronic_invoice(self):
        '''Downloads a ZIP containing an official XML and signed PDF
        document. This will only be available for invoices that have
        been successfully validated by Facturatech and the government.
        '''
        try:
            request = self._l10n_co_edi_create_ft_request()
            SEQUENCE_CODE = 'l10n_co_edi.filename'
            IrSequence = self.env['ir.sequence'].with_context(force_company=self.company_id.id)
            invoice_number = int(IrSequence.next_by_code(SEQUENCE_CODE)) + self.journal_id.l10n_co_edi_min_range_number
            response = request.download(self._l10n_co_edi_get_electronic_invoice_type_for_name(), invoice_number)
        except FacturatechZeepException as e:
            return _('Descarga de factura electrónica fallida. Mensaje de Facturatech:<br/>%s') % e, []
        except FacturatechWSException as e:
            raise UserError(e)
        else:
            return _('Descarga de factura electrónica exitosa. Mensaje de Facturatech:<br/>%s') % response['message'], [('%s.pdf' % self.name, response['zip_b64'])]

    def l10n_co_edi_check_status_electronic_invoice(self):
        '''This checks the current status of an uploaded XML with Facturatech. It
        posts the results in the invoice chatter and also attempts to
        download a ZIP containing the official XML and PDF if the
        invoice is reported as fully validated.
        '''
        for invoice in self:
            if not invoice.l10n_co_edi_transaction:
                raise Warning('La transacción no tiene establecido ID de transacción en Facturatech. (Cargue de factura electrónica exitosa)')
            request = invoice._l10n_co_edi_create_ft_request()
            try:
                response = request.check_status(invoice.l10n_co_edi_transaction)
            except FacturatechWSException as e:
                invoice.message_post(body=_('Revisión del estado de la factura en Facturatech falló. Mensaje de Facturatech:<br/>%s') % e)
            except FacturatechZeepException as e:
                invoice.message_post(body=_('Revisión del estado de la factura en Facturatech falló. Mensaje de Facturatech:<br/>%s') % e)
            else:
                if response['status'] == 'PROCESSING':
                    invoice.l10n_co_edi_invoice_status = 'processing'
                else:
                    invoice.l10n_co_edi_invoice_status = 'accepted' if response['legalStatus'] == 'SIGNED_XML' else 'rejected'

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
        invoice = super(AccountMove, self)._l10n_co_edi_generate_xml()
        #print(invoice)
        return invoice