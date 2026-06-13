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
            if inv.is_deposit_receive:
                extra['is_deposit_receive'] = True
                if inv.tenancy_id:
                    extra.setdefault('tenancy_id', inv.tenancy_id.id)
                if inv.property_id:
                    extra.setdefault('property_id', inv.property_id.id)
        payment = super()._create_payment(**extra)
        if not payment.mm_invoice_id and payment.reconciled_invoice_ids:
            inv = payment.reconciled_invoice_ids[:1]
            write_vals = {'mm_invoice_id': inv.id}
            if inv.is_deposit_receive:
                write_vals['is_deposit_receive'] = True
            payment.write(write_vals)
        payment._property_sync_customer_invoices_from_payment()
        return payment
