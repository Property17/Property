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
    _name = "report.pyment_report.mm_invoice_report"
    _description = "Inv Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        if len(docids) == 1:
            account_move = self.env['account.move'].search([('id', '=', docids)])
            if account_move.state != "blocked":
                tenancy = self.env['tenancy.rent.schedule'].search([('invoice_id', '=', account_move.id)])
                amount_paid = tenancy.amount - tenancy.rent_residual

                # num_word = ''
                # if self.env.lang == 'en_US':
                #     num_word = num2words(amount_paid, lang='en_US') + _(" only")
                # if self.env.lang == 'ar_001':
                num_word = num2words(amount_paid, lang='ar_001') + _(" فقط ")
                # num_word = amount_to_text_arabic(amount_paid, account_move.company_id.currency_id.name)

                ttyme = datetime.combine(fields.Date.from_string(account_move.invoice_date), time.min)
                locale = self.env.context.get('lang', 'en_US')
                date_name = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))

                return {
                    'property_manager': tenancy.tenancy_id.property_manager_id.name if tenancy.tenancy_id.property_manager_id.name else " ",
                    'company_st': tenancy.tenancy_id.property_manager_id.street if tenancy.tenancy_id.property_manager_id.street else " ",
                    'company_st2': tenancy.tenancy_id.property_manager_id.street2 if tenancy.tenancy_id.property_manager_id.street2 else " ",
                    'company_city': tenancy.tenancy_id.property_manager_id.city if tenancy.tenancy_id.property_manager_id.city else " ",
                    'country_name': tenancy.tenancy_id.property_manager_id.country_id.name if tenancy.tenancy_id.property_manager_id.country_id.name else " ",

                    'name': account_move.name if account_move.name else " ",
                    'contract_no': tenancy.tenancy_id.code if tenancy.tenancy_id.code else " ",
                    'invoice_date': account_move.invoice_date if account_move.invoice_date else " ",
                    'property_no': tenancy.tenancy_id.property_id.name if tenancy.tenancy_id.property_id.name else " ",
                    'auto_add_no': tenancy.tenancy_id.property_id.auto_add_no if tenancy.tenancy_id.property_id.auto_add_no else " ",
                    'partner_id': account_move.partner_id.name if account_move.partner_id.name else " ",
                    'date_name': date_name if date_name else " ",
                    'amount': tenancy.amount if tenancy.amount else " ",
                    'amount_paid': amount_paid if amount_paid else " ",
                    'invoice_payments_widget': account_move.invoice_payments_widget if account_move.invoice_payments_widget else " ",
                    'journal_id': account_move.mm_journal_id.name if account_move.mm_journal_id.name else " ",
                    'user_paid_by_id': account_move.user_paid_by_id.name if account_move.user_paid_by_id.name else " ",
                    'paid_date': account_move.paid_date if account_move.paid_date else " ",
                    'cheque_detail': account_move.cheque_detail if account_move.cheque_detail else " ",
                    'note': account_move.note if account_move.note else " ",
                    'rent_residual': tenancy.rent_residual if tenancy.rent_residual else " ",

                    'num_word': num_word,

                }
            else:
                raise ValidationError(_("You don't have accesses to print in this state"))
        else:
            raise ValidationError(_("You Should Select One Request Only"))