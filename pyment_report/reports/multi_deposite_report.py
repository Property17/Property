# -*- coding: utf-8 -*-
import babel
from datetime import datetime, time
from num2words import num2words

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class DepositeReportView(models.AbstractModel):
    _name = "report.pyment_report.mm_multi_deposite_report"
    _description = "Deposite Report"

    def _get_invoice_payment(self, move):
        """Posted payment reconciled with this customer invoice."""
        Payment = self.env['account.payment'].sudo()
        widget = move.invoice_payments_widget or {}
        for content in widget.get('content') or []:
            payment_id = content.get('account_payment_id')
            if payment_id:
                payment = Payment.browse(payment_id)
                if payment.exists() and payment.state == 'posted':
                    return payment
        if 'reconciled_invoice_ids' in Payment._fields:
            payment = Payment.search([
                ('reconciled_invoice_ids', 'in', move.ids),
                ('state', '=', 'posted'),
            ], limit=1, order='create_date desc, id desc')
            if payment:
                return payment
        return Payment.browse()

    def _get_move_tenancy(self, move):
        return move.tenancy_id or getattr(move, 'new_tenancy_id', False)

    def _amount_in_words(self, amount):
        if not amount:
            return num2words(0, lang='ar_001') + _(" فقط ")
        return num2words(amount, lang='ar_001') + _(" فقط ")

    def _get_property_manager(self, move, tenancy, property_rec):
        """Resolve property manager partner (asset uses ``property_manager``, tenancy uses ``property_manager_id``)."""
        if tenancy and tenancy.property_manager_id:
            return tenancy.property_manager_id
        if property_rec:
            manager = getattr(property_rec, 'property_manager_id', False) or getattr(
                property_rec, 'property_manager', False
            )
            if manager:
                return manager
        return self.env['res.partner']

    def _build_doc_from_deposit_invoice(self, move):
        """Deposit receive invoice (no rent schedule)."""
        tenancy = self._get_move_tenancy(move)
        payment = self._get_invoice_payment(move)
        property_rec = (
            move.property_id
            or (tenancy.property_id if tenancy else False)
        )
        manager = self._get_property_manager(move, tenancy, property_rec)
        amount_total = move.amount_total
        amount_paid = payment.amount if payment else (amount_total - move.amount_residual)
        deposit_value = tenancy.deposit if tenancy and tenancy.deposit else amount_total
        receipt_name = payment.name if payment else (move.name or '')
        paid_date = payment.date if payment else move.paid_date
        payment_method = ''
        if payment and payment.payment_method_line_id:
            payment_method = payment.payment_method_line_id.name
        elif move.payment_method_line_id:
            payment_method = move.payment_method_line_id.name
        payment_details = payment.ref if payment else (move.payment_reference or '')
        collector = ''
        if payment and payment.create_uid:
            collector = payment.create_uid.name
        elif getattr(move, 'user_paid_by_id', False):
            collector = move.user_paid_by_id.name
        elif move.invoice_user_id:
            collector = move.invoice_user_id.name
        properitis = move.properitis
        if not properitis and property_rec:
            properitis = property_rec.name
        return {
            'property_manager': manager.name if manager else '',
            'company_st': manager.street if manager else '',
            'company_st2': manager.street2 if manager else '',
            'company_city': manager.city if manager else '',
            'country_name': manager.country_id.name if manager and manager.country_id else '',
            'total_rent': tenancy.total_rent if tenancy else 0,
            'rent': deposit_value,
            'name': receipt_name,
            'contract_no': tenancy.code if tenancy else '',
            'invoice_date': move.invoice_date_due or move.invoice_date,
            'property_no': property_rec.name if property_rec else '',
            'auto_add_no': property_rec.auto_add_no if property_rec else '',
            'partner_id': move.partner_id.name,
            'date_name': '',
            'amount': deposit_value,
            'currency_id': move.currency_id.symbol,
            'amount_paid': amount_paid,
            'invoice_payments_widget': move.invoice_payments_widget,
            'journal_id': getattr(move, 'mm_journal_id', False) and move.mm_journal_id.name or '',
            'payment_method_line_id': payment_method,
            'user_paid_by_id': collector,
            'paid_date': paid_date,
            'cheque_detail': payment_details,
            'note': move.narration or '',
            'rent_residual': move.amount_residual,
            'invoice_user_id': collector,
            'num_word': self._amount_in_words(amount_paid),
            'payment_journal_id': getattr(move, 'payment_journal_id', False) and move.payment_journal_id.name or '',
            'properitis': properitis,
        }

    def _build_doc_from_rent_schedule(self, move, schedule):
        """Legacy path: deposit linked to a rent schedule invoice."""
        tenancy = schedule.tenancy_id
        amount_paid = schedule.amount - schedule.rent_residual
        ttyme = datetime.combine(
            fields.Date.from_string(move.invoice_date or fields.Date.today()),
            time.min,
        )
        locale = self.env.context.get('lang', 'en_US')
        date_name = tools.ustr(
            babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)
        )
        manager = self._get_property_manager(move, tenancy, tenancy.property_id if tenancy else False)
        return {
            'property_manager': manager.name if manager else '',
            'company_st': manager.street if manager else '',
            'company_st2': manager.street2 if manager else '',
            'company_city': manager.city if manager else '',
            'country_name': manager.country_id.name if manager and manager.country_id else '',
            'total_rent': tenancy.total_rent,
            'rent': tenancy.rent,
            'name': move.name,
            'contract_no': tenancy.code,
            'invoice_date': move.invoice_date,
            'property_no': tenancy.property_id.name,
            'auto_add_no': tenancy.property_id.auto_add_no,
            'partner_id': move.partner_id.name,
            'date_name': date_name,
            'amount': schedule.amount,
            'currency_id': move.currency_id.symbol,
            'amount_paid': amount_paid,
            'invoice_payments_widget': move.invoice_payments_widget,
            'journal_id': getattr(move, 'mm_journal_id', False) and move.mm_journal_id.name or '',
            'payment_method_line_id': (
                move.payment_method_line_id.name if move.payment_method_line_id else ''
            ),
            'user_paid_by_id': (
                move.user_paid_by_id.name if getattr(move, 'user_paid_by_id', False) else ''
            ),
            'paid_date': move.paid_date,
            'cheque_detail': schedule.cheque_detail,
            'note': schedule.note,
            'rent_residual': schedule.rent_residual,
            'invoice_user_id': move.invoice_user_id.name if move.invoice_user_id else '',
            'num_word': self._amount_in_words(amount_paid),
            'payment_journal_id': (
                getattr(move, 'payment_journal_id', False) and move.payment_journal_id.name or ''
            ),
            'properitis': move.properitis,
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        for move in self.env['account.move'].browse(docids):
            if move.state == 'blocked':
                raise ValidationError(_("You don't have accesses to print in this state"))
            is_deposit_invoice = getattr(move, 'is_deposit_receive', False)
            schedule = self.env['tenancy.rent.schedule'].search([
                ('invoice_id', '=', move.id),
            ], limit=1)
            if is_deposit_invoice or not schedule:
                docs.append(self._build_doc_from_deposit_invoice(move))
            else:
                docs.append(self._build_doc_from_rent_schedule(move, schedule))
        return {'docs': docs}
