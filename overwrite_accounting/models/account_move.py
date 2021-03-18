from odoo import models, fields
import datetime

# The original definition is done in account/models/account_move.py !


class AccountMove(models.Model):
    _inherit = "account.move"
    

    date_order = fields.Datetime(
        'Order Date', copy=False, help="Fecha de la orden de compra.")
    register_date = fields.Datetime(
        'Fecha de registro', copy=False, help="Fecha del registro de compra.", readonly=True)

    def get_taxes(self):
        taxes = {}
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                if taxes.get(tax.name) is None:
                    taxes[tax.name] = line.price_unit * \
                        tax.amount * line.quantity / 100
                else:
                    taxes[tax.name] += line.price_unit * \
                        tax.amount * line.quantity / 100
        return [(k, v) for k, v in taxes.items()]

    def action_post(self):
        super(AccountMove, self).action_post()
        mrp.write({'register_date': datetime.datetime.now()})

