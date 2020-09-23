# -*- coding: utf-8 -*-
# from odoo import http


# class ForceTranslate(http.Controller):
#     @http.route('/force_translate/force_translate/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/force_translate/force_translate/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('force_translate.listing', {
#             'root': '/force_translate/force_translate',
#             'objects': http.request.env['force_translate.force_translate'].search([]),
#         })

#     @http.route('/force_translate/force_translate/objects/<model("force_translate.force_translate"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('force_translate.object', {
#             'object': obj
#         })
