# -*- coding: utf-8 -*-
# from odoo import http


# class OverwriteHrPayroll(http.Controller):
#     @http.route('/overwrite_hr_payroll/overwrite_hr_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/overwrite_hr_payroll/overwrite_hr_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('overwrite_hr_payroll.listing', {
#             'root': '/overwrite_hr_payroll/overwrite_hr_payroll',
#             'objects': http.request.env['overwrite_hr_payroll.overwrite_hr_payroll'].search([]),
#         })

#     @http.route('/overwrite_hr_payroll/overwrite_hr_payroll/objects/<model("overwrite_hr_payroll.overwrite_hr_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('overwrite_hr_payroll.object', {
#             'object': obj
#         })
