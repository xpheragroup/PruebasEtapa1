import ast
import xlwt
import base64
from io import BytesIO
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception,content_disposition

class Binary(http.Controller):

    def _init_book(self):
        self.stream = BytesIO()
        self.book = xlwt.Workbook(encoding='utf-8')
        self.sheet = self.book.add_sheet(u'Reporte')
        for i in range(10):
            self.sheet.col(i).width = 7500
        self.position = 0

    def _finish_book(self):
        self.book.save(self.stream)
        data = self.stream.getvalue()
        self.stream.close()
        return data

    def _add_row(self, data):
        index = 0
        for piece in data:
            self.sheet.write(self.position, index, str(piece))
            index += 1
        self.position = self.position + 1


    @http.route('/web/binary/helisa_report', type='http', auth="public")
    @serialize_exception
    def download_document(self,ids,filename=None, **kw):
        self._init_book()

        model = http.request.env['account.move']
        res = model.browse(ast.literal_eval(ids))
        if not res:
            return request.not_found()

        self._add_row(['DOCUMENTO', 'FECHA', 'NIT', 'VALOR', 'NATURALEZA', 'CENTRO DE COSTO', 'CUENTA', 'No DOCUMENTO', 'DETALLE'])
        for invoice in res:
            for detail in invoice.invoice_line_ids:
                self._add_row([
                    'FC',
                    invoice.invoice_date or '' ,
                    invoice.partner_id.vat or '',
                    detail.debit if detail.debit > 0 else detail.credit,
                    'D' if detail.debit > 0 else 'C' ,
                    detail.analytic_account_id.name or '',
                    detail.account_id.code,
                    invoice.name,
                    detail.name
                ])
        
        filecontent = self._finish_book() 
        if not filename:
            filename = 'Helisa.xls'
        if not '.xls' in filename:
            filename += '.xls'
        return request.make_response(filecontent, [('Content-Type','application/octet-stream'), ('Content-Disposition', content_disposition(filename))])

    