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
                invoice.message_post(body=_('Electronic invoice status check failed. Message from Carvajal:<br/>%s') % e)
            else:
                if response['status'] == 'PROCESSING':
                    invoice.l10n_co_edi_invoice_status = 'processing'
                else:
                    invoice.l10n_co_edi_invoice_status = 'accepted' if response['legalStatus'] == 'ACCEPTED' else 'rejected'

                msg = _('Electronic invoice status check completed. Message from Carvajal:<br/>Status: %s') % response['status']
                attachments = []

                if response['errorMessage']:
                    msg += _('<br/>Error message: %s') % response['errorMessage'].replace('\n', '<br/>')
                if response['legalStatus']:
                    msg += _('<br/>Legal status: %s') % response['legalStatus']
                if response['governmentResponseDescription']:
                    msg += _('<br/>Government response: %s') % response['governmentResponseDescription']

                if invoice.l10n_co_edi_invoice_status == 'accepted':
                    invoice_download_msg, attachments = invoice.l10n_co_edi_download_electronic_invoice()
                    msg += '<br/><br/>' + invoice_download_msg

                invoice.message_post(body=msg, attachments=attachments)

    @api.model
    def _l10n_co_edi_check_processing_invoices(self):
        self.search([('l10n_co_edi_invoice_status', '=', 'processing')]).l10n_co_edi_check_status_electronic_invoice()
        return True

    def _l10n_co_edi_get_validation_time(self):
        '''Times should always be reported to Carvajal in Colombian time. This
        converts the validation time to that timezone.
        '''
        validation_time = self.l10n_co_edi_datetime_invoice
        validation_time = pytz.utc.localize(validation_time)

        bogota_tz = pytz.timezone('America/Bogota')
        validation_time = validation_time.astimezone(bogota_tz)

        return validation_time.strftime(DEFAULT_SERVER_TIME_FORMAT)

    def _l10n_co_edi_get_fiscal_values(self):
        commercial_partner = self.partner_id.commercial_partner_id
        return commercial_partner.l10n_co_edi_representation_type_id |\
            commercial_partner.l10n_co_edi_establishment_type_id |\
            commercial_partner.l10n_co_edi_obligation_type_ids |\
            commercial_partner.l10n_co_edi_customs_type_ids

    def _l10n_co_edi_get_partner_type(self, partner_id):
        if partner_id.is_company:
            return '3' if partner_id.l10n_co_edi_large_taxpayer else '1'
        else:
            return '2'

    def _l10n_co_edi_get_regime_code(self):
        return '0' if self.partner_id.commercial_partner_id.l10n_co_edi_simplified_regimen else '2'

    def _l10n_co_edi_get_sender_type_of_contact(self):
        return '2' if self.partner_id.commercial_partner_id.type == 'delivery' else '1'

    def _l10n_co_edi_get_total_units(self):
        '''Units have to be reported as units (not e.g. boxes of 12).'''
        lines = self.invoice_line_ids.filtered(lambda line: line.product_uom_id.category_id == self.env.ref('uom.product_uom_categ_unit'))
        units = 0

        for line in lines:
            units += line.product_uom_id._compute_quantity(line.quantity, self.env.ref('uom.product_uom_unit'))

        return int(units)

    def _l10n_co_edi_get_total_weight(self):
        '''Weight has to be reported in kg (not e.g. g).'''
        lines = self.invoice_line_ids.filtered(lambda line: line.product_uom_id.category_id == self.env.ref('uom.product_uom_categ_kgm'))
        kg = 0

        for line in lines:
            kg += line.product_uom_id._compute_quantity(line.quantity, self.env.ref('uom.product_uom_kgm'))

        return int(kg)

    def _l10n_co_edi_get_total_volume(self):
        '''Volume has to be reported in l (not e.g. ml).'''
        lines = self.invoice_line_ids.filtered(lambda line: line.product_uom_id.category_id == self.env.ref('uom.product_uom_categ_vol'))
        l = 0

        for line in lines:
            l += line.product_uom_id._compute_quantity(line.quantity, self.env.ref('uom.product_uom_litre'))

        return int(l)

    def _l10n_co_edi_get_notas(self):
        '''This generates notes in a particular format. These notes are pieces
        of text that are added to the PDF in various places. |'s are
        interpreted as newlines by Carvajal. Each note is added to the
        XML as follows:

        <NOT><NOT_1>text</NOT_1></NOT>

        One might wonder why Carvajal uses this arbitrary format
        instead of some extra simple XML tags but such questions are best
        left to philosophers, not dumb developers like myself.
        '''
        amount_in_words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(self.amount_total)
        shipping_partner = self.env['res.partner'].browse(self._get_invoice_delivery_partner_id())
        notas = [
            '1.-%s|%s|%s|%s|%s|%s' % (self.company_id.l10n_co_edi_header_gran_contribuyente or '',
                                      self.company_id.l10n_co_edi_header_tipo_de_regimen or '',
                                      self.company_id.l10n_co_edi_header_retenedores_de_iva or '',
                                      self.company_id.l10n_co_edi_header_autorretenedores or '',
                                      self.company_id.l10n_co_edi_header_resolucion_aplicable or '',
                                      self.company_id.l10n_co_edi_header_actividad_economica or ''),
            '2.-%s' % (self.company_id.l10n_co_edi_header_bank_information or '').replace('\n', '|'),
            '3.- %s' % (self.narration or 'N/A'),
            '6.- %s|%s' % (self.invoice_payment_term_id.note, amount_in_words),
            '7.- "%s" "- "%s"' % (self.company_id.website, self.company_id.phone),
            '8.-%s|%s|%s' % (self.partner_id.commercial_partner_id._get_vat_without_verification_code() or '', shipping_partner.phone or '', self.invoice_origin or ''),
            '10.- | | | |%s' % (self.invoice_origin or 'N/A'),
            '11.- |%s| |%s|%s' % (self._l10n_co_edi_get_total_units(), self._l10n_co_edi_get_total_weight(), self._l10n_co_edi_get_total_volume())
        ]

        return notas

    def _l10n_co_edi_get_electronic_invoice_type(self):
        INVOICE_TYPE_TO_ENC_1 = {
            'out_invoice': 'INVOIC',
            'in_invoice': 'INVOIC',
            'out_refund': 'NC',
            'in_refund': 'ND',
        }

        return INVOICE_TYPE_TO_ENC_1[self.type]

    def _l10n_co_edi_get_carvajal_code_for_document_type(self, partner):
        DOCUMENT_TYPE_TO_CARVAJAL_CODE = {
            'rut': '31',
            'id_card': '12',
            'national_citizen_id': '13',
            'id_document': '12',
            'passport': '41',

            'external_id': '21',
            'foreign_id_card': '22',
            'diplomatic_card': 'O-99',
            'residence_document': 'O-99',
            'civil_registration': '11',
        }

        document_type = partner.l10n_co_document_type
        return DOCUMENT_TYPE_TO_CARVAJAL_CODE[document_type] if document_type else ''

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

    def _l10n_co_edi_is_l10n_co_edi_required(self):
        self.ensure_one()
        return self.type in ('out_invoice', 'out_refund') and self.company_id.country_id == self.env.ref('base.co')

    def post(self):
        # OVERRIDE to generate the e-invoice for the Colombian Localization.
        res = super(AccountMove, self).post()

        to_process = self.filtered(lambda move: move._l10n_co_edi_is_l10n_co_edi_required())
        if to_process:
            to_process.write({'l10n_co_edi_datetime_invoice': fields.Datetime.now()})
            to_process.l10n_co_edi_upload_electronic_invoice()
        return res
