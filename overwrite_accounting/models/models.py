import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountJournal(models.Model):
    _inherit = "account.journal"

    # For Doris requirement
    # Size: 5 -> 10
    code = fields.Char(string='Short Code', size=10, required=True, help="Shorter name used for display. The journal entries of this journal will also be named using this prefix by default.")