from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    name = fields.Char(default='Nuevo')

    def print_quotation(self):
            self.write({'state': "sent"})
            return self.env.ref('overwrite_purchase.report_purchase_quotation').report_action(self)
    
    def get_taxes(self):
        taxes = {}
        for line in self.order_line:
            for tax in line.taxes_id:
                if taxes.get(tax.name) is None:
                    taxes[tax.name] = line.price_unit * tax.amount * line.product_qty / 100
                else:
                    taxes[tax.name] += line.price_unit * tax.amount * line.product_qty / 100
        return [(k, v) for k, v in taxes.items()]
