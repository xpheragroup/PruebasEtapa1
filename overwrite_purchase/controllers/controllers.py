# -*- coding: utf-8 -*-
# from odoo import http


# class OverwritePurchase(http.Controller):
#     @http.route('/overwrite_purchase/overwrite_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/overwrite_purchase/overwrite_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('overwrite_purchase.listing', {
#             'root': '/overwrite_purchase/overwrite_purchase',
#             'objects': http.request.env['overwrite_purchase.overwrite_purchase'].search([]),
#         })

#     @http.route('/overwrite_purchase/overwrite_purchase/objects/<model("overwrite_purchase.overwrite_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('overwrite_purchase.object', {
#             'object': obj
#         })
