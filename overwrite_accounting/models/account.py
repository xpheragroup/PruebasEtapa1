from odoo import models, fields

# The original definition is done in account/models/account.py !

class AccountJournal(models.Model):
    _inherit = "account.journal"        # Inherit class to make changes on account journal

    code = fields.Char(size=10)         # Short code is needed larger (size was 5, set 10)