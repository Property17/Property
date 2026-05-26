# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        Move = self.env['account.move']
        for vals in vals_list:
            move = Move.browse(vals.get('move_id')) if vals.get('move_id') else Move
            if move and getattr(move, 'is_deposit_receive', False):
                display_type = vals.get('display_type') or 'product'
                if display_type in ('line_section', 'line_note', 'payment_term'):
                    continue
                vals.pop('analytic_account_id', None)
                vals.pop('analytic_distribution', None)
                partner = move.partner_id
                if partner and partner.tenancy_insurance_id and not vals.get('account_id'):
                    vals['account_id'] = partner.tenancy_insurance_id.id
        lines = super().create(vals_list)
        lines._mm_apply_payment_tenancy_analytic()
        lines._mm_apply_deposit_receive_invoice_lines()
        return lines

    def write(self, vals):
        if self.env.context.get('mm_skip_deposit_line_sync'):
            return super().write(vals)
        res = super().write(vals)
        if vals.get('move_id') or vals.get('account_id') or vals.get('analytic_account_id'):
            self.with_context(mm_skip_deposit_line_sync=True)._mm_apply_deposit_receive_invoice_lines()
        return res

    def _mm_deposit_receive_product_line(self, line):
        """Only invoice product lines get the insurance account (not receivable/payable terms)."""
        if line.display_type in ('line_section', 'line_note', 'payment_term'):
            return False
        if line.account_id.account_type in ('asset_receivable', 'liability_payable'):
            return False
        return True

    def _mm_apply_deposit_receive_invoice_lines(self):
        """Deposit receive invoice: insurance account on product line only; no tenancy analytic."""
        for line in self:
            move = line.move_id
            if not getattr(move, 'is_deposit_receive', False):
                continue
            if not self._mm_deposit_receive_product_line(line):
                continue
            partner = move.partner_id
            updates = {}
            if partner and partner.tenancy_insurance_id:
                updates['account_id'] = partner.tenancy_insurance_id.id
            if line.analytic_account_id or line.analytic_distribution:
                updates['analytic_account_id'] = False
                updates['analytic_distribution'] = False
            if 'tenancy_id' in line._fields and line.tenancy_id:
                updates['tenancy_id'] = False
            if updates:
                line.with_context(mm_skip_deposit_line_sync=True).write(updates)

    def _mm_apply_payment_tenancy_analytic(self):
        """Mirror AccountPaymentInhNew._prepare_move_line_default_vals: credit lines on
        payment moves get tenancy analytic from account.payment when not deposit receive.
        """
        for line in self:
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
                line.with_context(mm_skip_deposit_line_sync=True).write(updates)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        res = super().write(vals)
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

