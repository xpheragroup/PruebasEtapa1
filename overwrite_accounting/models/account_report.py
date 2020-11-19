# No member error in this file are for inheritance in Odoo!
# pylint: disable=E1101

from odoo import models, _
from odoo.exceptions import ValidationError, UserError

# The original definition is done in account_report_cash_basis/models/account_report.py !

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

class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label))\
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids')\
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id)\
                    .reconcile()
            if rec.invoice_ids:
                for invoice in rec.invoice_ids:
                    # TODO: Define x_studio_consecutivos_de_caja as invoice model field 
                    invoice.x_studio_consecutivos_de_caja = rec.x_studio_consecutivo_de_caja
        return True