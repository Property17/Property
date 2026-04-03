# See LICENSE file for full copyright and licensing details

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _create_payment(self, **extra_create_values):
        payment = super()._create_payment(**extra_create_values)
        payment._property_sync_customer_invoices_from_payment()
        return payment
