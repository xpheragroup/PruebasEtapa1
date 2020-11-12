# -*- coding: utf-8 -*-
# from odoo import http


# class L10nCoEdiFt(http.Controller):
#     @http.route('/l10n_co_edi_ft/l10n_co_edi_ft/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_co_edi_ft/l10n_co_edi_ft/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_co_edi_ft.listing', {
#             'root': '/l10n_co_edi_ft/l10n_co_edi_ft',
#             'objects': http.request.env['l10n_co_edi_ft.l10n_co_edi_ft'].search([]),
#         })

#     @http.route('/l10n_co_edi_ft/l10n_co_edi_ft/objects/<model("l10n_co_edi_ft.l10n_co_edi_ft"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_co_edi_ft.object', {
#             'object': obj
#         })
