# -*- coding: utf-8 -*-
import json
from num2words import num2words
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import date, datetime, time
from odoo.exceptions import UserError, ValidationError
from .money_to_text_ar import amount_to_text_arabic


class InvReportView(models.AbstractModel):
    _name = "report.pyment_report.mm_multi_invoice_report"
    _description = "Inv Report"

    @api.model
    def _parse_invoice_payments_widget(self, move):
        widget = move.invoice_payments_widget
        if not widget:
            return []
        if isinstance(widget, (bytes, bytearray)):
            try:
                widget = json.loads(widget.decode())
            except (ValueError, TypeError, AttributeError):
                return []
        if isinstance(widget, str):
            try:
                widget = json.loads(widget)
            except (ValueError, TypeError):
                return []
        if not isinstance(widget, dict):
            return []
        return widget.get('content') or []

    @api.model
    def _get_invoice_payment_widget_line(self, move, payment_id=None):
        """Reconciled payment line from the invoice widget (portal can pass payment_id)."""
        content = self._parse_invoice_payments_widget(move)
        if payment_id:
            for line in content:
                if line.get('account_payment_id') == payment_id:
                    return line
        return content[0] if content else None

    @api.model
    def _get_first_invoice_payment_widget_line(self, move):
        return self._get_invoice_payment_widget_line(move)

    @api.model
    def _format_widget_payment_date(self, date_val):
        if not date_val:
            return False
        if isinstance(date_val, str):
            return date_val
        if isinstance(date_val, date):
            return fields.Date.to_string(date_val)
        return str(date_val)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        account_move = self.env['account.move'].browse(docids)
        for move in account_move:
            if move.state != "blocked":
                tenancy = self.env['tenancy.rent.schedule'].search([('invoice_id', '=', move.id)])
                portal_payment_id = self.env.context.get('portal_payment_id')
                first_widget_line = self._get_invoice_payment_widget_line(
                    move, portal_payment_id,
                )
                widget_content = self._parse_invoice_payments_widget(move)
                if portal_payment_id and first_widget_line:
                    amount_paid = first_widget_line.get('amount', 0) or 0
                    cumulative = 0.0
                    rent_residual = tenancy.rent_residual
                    for line in widget_content:
                        cumulative += line.get('amount', 0) or 0
                        if line.get('account_payment_id') == portal_payment_id:
                            rent_residual = max((tenancy.amount or 0) - cumulative, 0)
                            break
                else:
                    amount_paid = tenancy.amount - tenancy.rent_residual
                    rent_residual = tenancy.rent_residual
                num_word = num2words(amount_paid, lang='ar_001') + _(" فقط ")

                ttyme = datetime.combine(fields.Date.from_string(move.invoice_date), time.min)
                locale = self.env.context.get('lang', 'en_US')
                date_name = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))
                paid_date = move.paid_date
                if not paid_date and first_widget_line:
                    paid_date = self._format_widget_payment_date(first_widget_line.get('date'))
                payment_method_name = move.payment_method_line_id.name if move.payment_method_line_id else ''
                if not payment_method_name and first_widget_line:
                    payment_method_name = (
                        first_widget_line.get('payment_method_name')
                        or first_widget_line.get('journal_name')
                        or ''
                    )
                payment_details = move.payment_reference or getattr(move, 'cheque_detail', '') or ''
                if not payment_details and first_widget_line:
                    payment_details = first_widget_line.get('ref') or ''
                # Pass the move on each doc so web.external_layout can set company/logo from
                # move.company_id (portal PDF uses sudo(); env.company would be wrong).
                docs.append({
                    'move': move,
                    'property_manager': tenancy.tenancy_id.property_manager_id.name,
                    'company_st': tenancy.tenancy_id.property_manager_id.street,
                    'company_st2': tenancy.tenancy_id.property_manager_id.street2,
                    'company_city': tenancy.tenancy_id.property_manager_id.city,
                    'country_name': tenancy.tenancy_id.property_manager_id.country_id.name,

                    'name': move.name,
                    'contract_no': tenancy.tenancy_id.code,
                    'invoice_date': move.invoice_date,
                    'property_no': tenancy.tenancy_id.property_id.name,
                    'auto_add_no': tenancy.tenancy_id.property_id.auto_add_no,
                    'partner_id': move.partner_id.name,
                    'date_name': date_name,
                    'amount': tenancy.amount,
                    'amount_paid': amount_paid,
                    'currency_id': move.currency_id.symbol,
                    'invoice_payments_widget': move.invoice_payments_widget,
                    'journal_id': move.mm_journal_id.name,
                    'user_paid_by_id': move.user_paid_by_id.name,
                    'paid_date': paid_date,
                    'cheque_detail': payment_details,
                    'note': move.note,
                    'rent_residual': rent_residual,
                    'invoice_user_id': move.invoice_user_id.name,
                    'num_word': num_word,
                    'payment_journal_id': move.payment_journal_id.name,
                    'payment_method_line_id': payment_method_name,
                    'properitis': move.properitis,


                })

            else:
                raise ValidationError(_("You don't have accesses to print in this state"))

        return {
            'docs': docs,
        }