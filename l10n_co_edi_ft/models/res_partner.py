# coding: utf-8
from odoo import api, fields, models, _\

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_vat_without_verification_code(self):
        self.ensure_one()
        # last digit is the verification code
        return self.vat.split('-')[0] if self.vat else ''