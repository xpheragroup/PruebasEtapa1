from odoo import models, fields

# The original definition is done in account/models/account_move.py !

class AccountMove(models.Model):
    _inherit = "account.move"

    date_order = fields.Datetime('Order Date', copy=False, help="Fecha de la orden de compra.")