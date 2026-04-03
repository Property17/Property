# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _property_payment_link_tenancy_ids(self):
        """Tenancy analytic accounts linked to this move (rent uses tenancy_id and/or new_tenancy_id)."""
        self.ensure_one()
        Tenancy = self.env['account.analytic.account']
        tenancies = Tenancy.browse()
        if self.tenancy_id:
            tenancies |= self.tenancy_id
        if self.new_tenancy_id:
            tenancies |= self.new_tenancy_id
        return tenancies

    def _check_tenancy_payments_not_blocked(self):
        """Raise if any linked property tenancy blocks payments (matches portal / transaction rules)."""
        for move in self.filtered(lambda m: m.is_invoice(include_receipts=True)):
            for tenancy in move._property_payment_link_tenancy_ids():
                if tenancy.is_blocked or tenancy.state == 'blocked':
                    raise UserError(_(
                        'You cannot register a payment for invoice %(invoice)s because payments are '
                        'blocked for tenancy "%(tenancy)s". Unblock the tenancy or contact the property manager.',
                    ) % {
                        'invoice': move.display_name,
                        'tenancy': tenancy.display_name,
                    })


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def action_register_payment(self):
        self.mapped('move_id')._check_tenancy_payments_not_blocked()
        return super().action_register_payment()


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        self.line_ids.move_id._check_tenancy_payments_not_blocked()
        return super()._create_payments()
