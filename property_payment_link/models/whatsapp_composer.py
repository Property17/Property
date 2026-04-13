# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import ValidationError, RedirectWarning
from odoo.addons.whatsapp.tools import phone_validation as wa_phone_validation


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

    @api.depends('phone', 'batch_mode', 'res_ids', 'wa_template_id')
    def _compute_invalid_phone_number_count(self):
        """Property payment link bulk: validate using tenant partner country (enterprise used link record)."""
        custom = self.filtered(
            lambda c: c.res_model == 'property.payment.link' and c.batch_mode and c.wa_template_id
        )
        for composer in custom:
            records = composer._get_active_records()
            invalid = 0
            for rec in records:
                if composer.wa_template_id.phone_field:
                    mobile_number = rec._find_value_from_field_path(
                        composer.wa_template_id.phone_field
                    )
                else:
                    mobile_number = ''
                if not mobile_number or not str(mobile_number).strip():
                    mobile_number = rec._get_whatsapp_tenant_number()
                formatted = (
                    rec._whatsapp_format_phone_number(mobile_number, raise_exception=False)
                    if mobile_number
                    else False
                )
                if not formatted:
                    invalid += 1
            composer.invalid_phone_number_count = invalid
        # Standard whatsapp.composer logic (cannot super() reliably across _inherit merges).
        for composer in self - custom:
            records = composer._get_active_records()
            if composer.batch_mode:
                invalid_phone_number_count = 0
                for rec in records:
                    mobile_number = rec._find_value_from_field_path(
                        composer.wa_template_id.phone_field
                    )
                    mobile_number = (
                        wa_phone_validation.wa_phone_format(
                            rec,
                            number=mobile_number or '',
                            raise_exception=False,
                        )
                        if mobile_number
                        else False
                    )
                    if not mobile_number:
                        invalid_phone_number_count += 1
            elif composer.phone:
                sanitize_number = wa_phone_validation.wa_phone_format(
                    records,
                    number=composer.phone,
                    raise_exception=False,
                )
                invalid_phone_number_count = 1 if not sanitize_number else 0
            else:
                invalid_phone_number_count = 1
            composer.invalid_phone_number_count = invalid_phone_number_count

    def _send_whatsapp_template(self, force_send_by_cron=False):
        """Format numbers with tenant country for property.payment.link (single and bulk)."""
        self.ensure_one()
        if self.res_model != 'property.payment.link':
            return super()._send_whatsapp_template(force_send_by_cron=force_send_by_cron)

        records = self._get_active_records()
        if self.wa_template_id and self.wa_template_id.variable_ids:
            field_types = self.wa_template_id.variable_ids.mapped('field_type')
            if 'user_mobile' in field_types and not self.env.user.mobile:
                raise ValidationError(
                    _('User mobile number required in template but no value set on user profile.')
                )
        free_text_json = self._get_text_free_json()
        message_vals = []
        raise_exception = False if self.batch_mode or force_send_by_cron else True
        for rec in records:
            if self.batch_mode:
                mobile_number = rec._find_value_from_field_path(self.wa_template_id.phone_field)
                if not mobile_number or not str(mobile_number).strip():
                    mobile_number = rec._get_whatsapp_tenant_number()
            else:
                mobile_number = self.phone
                if not mobile_number or not str(mobile_number).strip():
                    mobile_number = rec._get_whatsapp_tenant_number()
            formatted_number_wa = rec._whatsapp_format_phone_number(
                mobile_number,
                raise_exception=raise_exception,
            )
            if not (formatted_number_wa or force_send_by_cron):
                continue
            body = self._get_html_preview_whatsapp(rec=rec)
            post_values = {
                'attachment_ids': [self.attachment_id.id] if self.attachment_id else [],
                'body': body,
                'message_type': 'whatsapp_message',
                'partner_ids': hasattr(records, '_mail_get_partners') and rec._mail_get_partners()[rec.id].ids or rec._whatsapp_get_responsible().partner_id.ids,
            }
            if hasattr(records, '_message_log'):
                message = rec._message_log(**post_values)
            else:
                message = self.env['mail.message'].create(
                    dict(
                        post_values,
                        res_id=rec.id,
                        model=self.res_model,
                        subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                    )
                )
            message_vals.append({
                'mail_message_id': message.id,
                'mobile_number': mobile_number,
                'mobile_number_formatted': formatted_number_wa,
                'free_text_json': free_text_json,
                'wa_template_id': self.wa_template_id.id,
                'wa_account_id': self.wa_template_id.wa_account_id.id,
            })
        if message_vals:
            messages = self.env['whatsapp.message'].create(message_vals)
            messages._send(force_send_by_cron=force_send_by_cron)
            return messages
        return self.env['whatsapp.message']
