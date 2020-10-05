# -*- coding: utf-8 -*-
# from odoo import http


# class OverwriteAccounting(http.Controller):
#     @http.route('/overwrite_accounting/overwrite_accounting/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/overwrite_accounting/overwrite_accounting/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('overwrite_accounting.listing', {
#             'root': '/overwrite_accounting/overwrite_accounting',
#             'objects': http.request.env['overwrite_accounting.overwrite_accounting'].search([]),
#         })

#     @http.route('/overwrite_accounting/overwrite_accounting/objects/<model("overwrite_accounting.overwrite_accounting"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('overwrite_accounting.object', {
#             'object': obj
#         })
