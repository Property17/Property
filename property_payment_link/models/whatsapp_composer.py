# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import ValidationError, RedirectWarning


def _payment_link_context_doc_ids(context):
    """Stable list of property.payment.link ids from action context (list views can pass tuple/empty)."""
    ids = context.get('active_ids')
    if ids is None:
        ids = []
    elif isinstance(ids, (tuple, set)):
        ids = list(ids)
    elif not isinstance(ids, list):
        ids = [ids]
    ids = [i for i in ids if i]
    if not ids and context.get('active_id'):
        ids = [context['active_id']]
    return ids


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
            ids = _payment_link_context_doc_ids(context)
            result = {
                'res_model': context['active_model'],
                'wa_template_id': context['default_wa_template_id'],
                'res_ids': str(ids),
                'batch_mode': len(ids) > 1,
            }
            return result

        # Ensure res_ids is a string for property.payment.link (Char field + literal_eval in composer).
        # Enterprise default_get may leave res_ids as a list; bulk would then break _compute_number.
        context = self.env.context
        if context.get('active_model') == 'property.payment.link':
            ids = _payment_link_context_doc_ids(context)
            if ids:
                result['res_ids'] = str(ids)
                result['batch_mode'] = len(ids) > 1
            else:
                rid = result.get('res_ids')
                if isinstance(rid, (list, tuple)):
                    norm = [i for i in rid if i]
                    result['res_ids'] = str(norm)
                    result['batch_mode'] = len(norm) > 1
                elif rid is not None and not isinstance(rid, str):
                    result['res_ids'] = str([rid])
                    result['batch_mode'] = False
        return result
