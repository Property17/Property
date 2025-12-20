# -*- coding: utf-8 -*-
import json
from num2words import num2words
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import date, datetime, time
from odoo.exceptions import UserError, ValidationError
from .money_to_text_ar import amount_to_text_arabic


class DepositeReportView(models.AbstractModel):
    _name = "report.pyment_report.mm_multi_deposite_report"
    _description = "Deposite Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        account_move = self.env['account.move'].browse(docids)
        for move in account_move:
            if move.state != "blocked":
                tenancy = self.env['tenancy.rent.schedule'].search([('invoice_id', '=', move.id)])
                amount_paid = tenancy.amount - tenancy.rent_residual

                num_word = num2words(amount_paid, lang='ar_001') + _(" فقط ")

                ttyme = datetime.combine(fields.Date.from_string(move.invoice_date), time.min)
                locale = self.env.context.get('lang', 'en_US')
                date_name = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))

                docs.append({
                    'property_manager': tenancy.tenancy_id.property_manager_id.name,
                    'company_st': tenancy.tenancy_id.property_manager_id.street,
                    'company_st2': tenancy.tenancy_id.property_manager_id.street2,
                    'company_city': tenancy.tenancy_id.property_manager_id.city,
                    'country_name': tenancy.tenancy_id.property_manager_id.country_id.name,
                    'total_rent': tenancy.tenancy_id.total_rent,
                    'rent': tenancy.tenancy_id.rent,

                    'name': move.name,
                    'contract_no': tenancy.tenancy_id.code,
                    'invoice_date': move.invoice_date,
                    'property_no': tenancy.tenancy_id.property_id.name,
                    'auto_add_no': tenancy.tenancy_id.property_id.auto_add_no,
                    'partner_id': move.partner_id.name,
                    'date_name': date_name,
                    'amount': tenancy.amount,
                    'currency_id': move.currency_id.symbol,
                    'amount_paid': amount_paid,
                    'invoice_payments_widget': move.invoice_payments_widget,
                    'journal_id': move.mm_journal_id.name,
                    'payment_method_line_id': move.payment_method_line_id.name,
                    'user_paid_by_id': move.user_paid_by_id.name,
                    'paid_date': move.paid_date,
                    'cheque_detail': tenancy.cheque_detail,
                    'note': tenancy.note,
                    'rent_residual': tenancy.rent_residual,
                    'invoice_user_id': move.invoice_user_id.name,
                    'num_word': num_word,
                    'payment_journal_id': move.payment_journal_id.name,
                    'invoice_user_id': move.invoice_user_id.name,
                    'properitis': move.properitis,
                    

                })

            else:
                raise ValidationError(_("You don't have accesses to print in this state"))

        return {
            'docs': docs,
        }