# See LICENSE file for full copyright and licensing details

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _create_payment(self, **extra_create_values):
        """Pass linked invoice(s) on the payment before post so compute / propagate run in time for journal items.

        Provider flows (e.g. MyFatoorah) never use the register-payment wizard, so ``mm_invoice_id`` was empty,
        ``compute_mm_move_id`` did not run, and ``tenancy_id`` was missing during ``action_post()``.
        """
        self.ensure_one()
        extra = dict(extra_create_values or {})
        if self.operation == self.source_transaction_id.operation:
            invoices = self.source_transaction_id.invoice_ids
        else:
            invoices = self.invoice_ids
        inv = invoices[:1]
        if inv:
            extra.setdefault('mm_invoice_id', inv.id)
        payment = super()._create_payment(**extra)
        if not payment.mm_invoice_id and payment.reconciled_invoice_ids:
            payment.write({'mm_invoice_id': payment.reconciled_invoice_ids.ids[0]})
        payment._property_sync_customer_invoices_from_payment()
        return payment
