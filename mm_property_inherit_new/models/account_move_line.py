# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._mm_apply_payment_tenancy_analytic()
        return lines

    def _mm_apply_payment_tenancy_analytic(self):
        """Mirror AccountPaymentInhNew._prepare_move_line_default_vals: credit lines on
        payment moves get tenancy analytic from account.payment when not deposit receive.
        """
        for line in self:
            # Prefer the direct payment_id on the line (stored related) in case
            # the move/payment link isn't written yet.
            payment = getattr(line, 'payment_id', False) or line.move_id.payment_id
            if not payment:
                continue
            tenancy = getattr(payment, 'tenancy_id', False)
            if not tenancy:
                continue
            if getattr(payment, 'is_deposit_receive', False):
                continue
            updates = {}
            if not line.analytic_account_id:
                updates['analytic_account_id'] = tenancy.id
            if 'tenancy_id' in line._fields and not line.tenancy_id:
                updates['tenancy_id'] = tenancy.id
            if updates:
                line.write(updates)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        res = super().write(vals)
        # Payment registration writes payment_id and line_ids together; lines may be
        # created before payment_id is visible on the move until this write completes.
        if vals.get('payment_id') or vals.get('line_ids'):
            self.filtered(
                lambda m: m.payment_id and getattr(m.payment_id, 'tenancy_id', False)
            )._mm_propagate_payment_tenancy_to_lines()
        return res

    def _mm_propagate_payment_tenancy_to_lines(self):
        for move in self:
            payment = move.payment_id
            if getattr(payment, 'is_deposit_receive', False):
                continue
            for line in move.line_ids:
                updates = {}
                if not line.analytic_account_id:
                    updates['analytic_account_id'] = payment.tenancy_id.id
                if 'tenancy_id' in line._fields and not line.tenancy_id:
                    updates['tenancy_id'] = payment.tenancy_id.id
                if updates:
                    line.write(updates)
