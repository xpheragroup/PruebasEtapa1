# coding: utf-8
import base64
import logging
import os
import pytz
import socket
import re
from datetime import datetime
from hashlib import sha256
from odoo import _
from zeep import Client, Plugin
from zeep.exceptions import Fault
from zeep.wsse.username import UsernameToken

from lxml import etree

_logger = logging.getLogger(__name__)
# uncomment to enable logging of Zeep requests and responses
logging.getLogger('zeep.transports').setLevel(logging.DEBUG)

class FacturatechException(Exception):
    pass

class FacturatechPlugin(Plugin):

    def log(self, xml, func):
        _logger.debug('%s with\n%s' % (func, etree.tostring(xml, encoding='utf-8', xml_declaration=True, pretty_print=True)))

    def egress(self, envelope, http_headers, operation, binding_options):
        self.log(envelope, 'facturatech_request')
        return envelope, http_headers

    def ingress(self, envelope, http_headers, operation):
        self.log(envelope, 'facturatech_response')
        return envelope, http_headers

class FacturatechUsernameToken(UsernameToken):
    def _create_password_digest(self):
        """Factura expects a password hashed"""
        res = super(FacturatechUsernameToken, self)._create_password_digest()
        res[0].attrib['Type'] = res[0].attrib['Type'].replace('PasswordDigest', 'PasswordText')
        return res

class FacturatechRequest():
    def __init__(self, username, password, company, account, test_mode):
        self.username = username or ''
        self.password = password or ''

        token = self._create_wsse_header(self.username, self.password)
        self.client = Client('https://ws.facturatech.co/%s/index.php?wsdl' % ('21' if test_mode else '21Pro'), plugins=[FacturatechPlugin()], wsse=token)

    def _create_wsse_header(self, username, password):

        created = datetime.now()
        token = FacturatechUsernameToken(username=username, password_digest=password.encode(), use_digest=True, created=created)

        return token

    def upload(self, filename, xml):
        try:
            response = self.client.service['FtechAction.uploadInvoiceFile'](xmlBase64=base64.b64encode(xml).decode())
        except Fault as fault:
            _logger.error(fault)
            raise FacturatechException(fault)
        except socket.timeout as e:
            _logger.error(e)
            raise FacturatechException(_('Connection to Facturatech timed out. Their API is probably down.'))

        return {
            'message': 'success: %s, error: %s' % (response.success, response.error),
            'transactionId': response.transaccionID,
        }

    def download(self, document_prefix, document_number, document_type):
        try:
            response = self.client.service['FtechAction.downloadPDFFile'](prefijo=document_prefix,
                                                                          folio=document_number)
        except Fault as fault:
            _logger.error(fault)
            raise FacturatechException(fault)
        return {
            'message': 'success: %s, error: %s' % (response.success, response.error),
            'zip_b64': base64.b64decode(response.resourceData),
        }

    def check_status(self, transactionId):
        try:
            response = self.client.service.DocumentStatus(transactionId=transactionId)
        except Fault as fault:
            _logger.error(fault)
            raise FacturatechException(fault)
        return {
            'status': response.success,
            'errorMessage': response.error,
            'legalStatus': response.status,
            'governmentResponseDescription': response.governmentResponseDescription if hasattr(response, 'governmentResponseDescription') else '',
        }
