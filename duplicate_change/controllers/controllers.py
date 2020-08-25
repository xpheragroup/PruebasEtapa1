# -*- coding: utf-8 -*-
# from odoo import http


# class DuplicateChange(http.Controller):
#     @http.route('/duplicate_change/duplicate_change/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/duplicate_change/duplicate_change/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('duplicate_change.listing', {
#             'root': '/duplicate_change/duplicate_change',
#             'objects': http.request.env['duplicate_change.duplicate_change'].search([]),
#         })

#     @http.route('/duplicate_change/duplicate_change/objects/<model("duplicate_change.duplicate_change"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('duplicate_change.object', {
#             'object': obj
#         })
