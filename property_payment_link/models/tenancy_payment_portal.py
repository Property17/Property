# -*- coding: utf-8 -*-
from odoo import models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    def _payment_link_get_unpaid_deposit_invoices(self):
        """Posted customer deposit invoices with amount due (``acc_inv_dep_rec_id`` and related)."""
        self.ensure_one()
        Move = self.env['account.move'].sudo()
        invoices = Move.browse()
        if 'acc_inv_dep_rec_id' in self._fields and self.acc_inv_dep_rec_id:
            invoices |= self.acc_inv_dep_rec_id
        if 'is_deposit_receive' in Move._fields:
            invoices |= Move.search([
                ('tenancy_id', '=', self.id),
                ('move_type', '=', 'out_invoice'),
                ('is_deposit_receive', '=', True),
                ('state', '=', 'posted'),
            ])
        return invoices.filtered(
            lambda inv: inv.amount_residual > 0 and inv.state == 'posted'
        )
