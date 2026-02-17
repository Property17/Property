# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import ValidationError, RedirectWarning


class WhatsAppComposer(models.TransientModel):
    _inherit = 'whatsapp.composer'

    @api.model
    def default_get(self, fields):
        try:
            result = super().default_get(fields)
        except (ValidationError, RedirectWarning):
            context = self.env.context
            if context.get('active_model') != 'property.payment.link' or not context.get('default_wa_template_id'):
                raise
            result = {
                'res_model': context['active_model'],
                'wa_template_id': context['default_wa_template_id'],
                'res_ids': str(context.get('active_ids') or [context.get('active_id')]),
                'batch_mode': bool(context.get('active_ids') and len(context.get('active_ids', [])) > 1),
            }
            return result

        # Ensure res_ids is a string for property.payment.link (Char field expects string, literal_eval needs it)
        context = self.env.context
        if context.get('active_model') == 'property.payment.link' and (context.get('active_ids') or context.get('active_id')):
            ids = context.get('active_ids') or [context.get('active_id')]
            result['res_ids'] = str(ids) if not isinstance(ids, str) else ids
            result['batch_mode'] = len(ids) > 1
        return result
