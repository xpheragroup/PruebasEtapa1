import re
from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
from collections import defaultdict
from odoo.exceptions import ValidationError, UserError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class AccountMove(models.Model):
    _inherit = "account.move"

    date_order = fields.Datetime('Order Date', copy=False, help="Fecha de la orden de compra.")
class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    MOST_SORT_PRIO = 0
    LEAST_SORT_PRIO = 99

    # Create codes path in the hierarchy based on account.
    def get_account_codes(self, account):
        # A code is tuple(sort priority, actual code)
        codes = []
        if account.group_id:
            group = account.group_id
            while group:
                code = '%s %s' % (group.code_prefix or '', group.name)
                codes.append((self.MOST_SORT_PRIO, code))
                group = group.parent_id
        else:
            codes.append((self.MOST_SORT_PRIO, account.code[:4]))
            codes.append((self.MOST_SORT_PRIO, account.code[:2]))
            codes.append((self.MOST_SORT_PRIO, account.code[:1]))
        return list(reversed(codes))

    def _init_filter_multi_company(self, options, previous_options=None):
        if not self.filter_multi_company:
            return

        companies = self.env.user.company_ids
        if len(companies) > 1:
            allowed_company_ids = self._context.get('allowed_company_ids', self.env.company.ids)
            options['multi_company'] = [
                {'id': c.id, 'name': c.name, 'selected': c.id in allowed_company_ids, 'vat': c.vat} for c in companies
            ]

class PaymentRegister(models.TransientModel):
    _inherit= 'account.payment.register'
    consecutivo_de_caja = fields.Char( string='Consecutivo de caja')
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices/bills to pay. In case of multiple
            documents, they need to be grouped by partner, bank, journal and
            currency.
        :return: The payment values as a dictionary.
        '''
        amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date)
        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self._prepare_communication(invoices),
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': ('inbound' if amount > 0 else 'outbound'),
            'amount': abs(amount),
            'currency_id': invoices[0].currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': invoices[0].invoice_partner_bank_id.id,
            'x_studio_consecutivo_de_caja': self.consecutivo_de_caja,
        }
        return values
   