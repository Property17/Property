# -*- coding: utf-8 -*-

from odoo import models


class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    def _send(self, force_send_by_cron=False):
        """For property.payment.link bulk: send immediately instead of queuing (cron runs hourly).

        Use a filtered subset so one bad row does not force the whole batch onto cron; send the rest
        via the standard path.
        """
        prop_msgs = self.filtered(
            lambda m: m.mail_message_id
            and m.mail_message_id.model == 'property.payment.link'
        )
        other = self - prop_msgs
        if len(prop_msgs) > 1:
            prop_msgs._send_message(with_commit=False)
            if other:
                super(WhatsAppMessage, other)._send(force_send_by_cron=force_send_by_cron)
            return
        super()._send(force_send_by_cron=force_send_by_cron)
