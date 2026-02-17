# -*- coding: utf-8 -*-

from odoo import models


class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    def _send(self, force_send_by_cron=False):
        """For property.payment.link bulk: send immediately instead of queuing (cron runs hourly)."""
        if self and len(self) > 1 and all(
            m.mail_message_id and m.mail_message_id.model == 'property.payment.link' for m in self
        ):
            self._send_message(with_commit=False)
        else:
            super()._send(force_send_by_cron=force_send_by_cron)
