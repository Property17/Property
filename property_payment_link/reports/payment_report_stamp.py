# -*- coding: utf-8 -*-

from odoo import api, models


class ReportMultiInvoice(models.AbstractModel):
    _inherit = 'report.pyment_report.mm_multi_invoice_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data)
        RentSchedule = self.env['tenancy.rent.schedule']
        Company = self.env['res.company']
        for doc in res.get('docs') or []:
            move = doc.get('move')
            if not move:
                continue
            schedule = RentSchedule.search([('invoice_id', '=', move.id)], limit=1)
            tenancy = schedule.tenancy_id if schedule else False
            doc['stamp_data_uri'] = Company.get_stamp_data_uri(move=move, tenancy=tenancy)
        return res


class ReportPaymentDepositePortal(models.AbstractModel):
    _name = 'report.pyment_report.report_payment_deposite_document_portal'
    _description = 'Deposit receipt (portal) with company stamp'

    @api.model
    def _get_report_values(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids).sudo()
        Company = self.env['res.company']
        stamp_by_payment_id = {}
        for payment in payments:
            tenancy = payment.tenancy_id
            if not tenancy and payment.reconciled_invoice_ids:
                tenancy = payment.reconciled_invoice_ids[:1].tenancy_id
            move = payment.reconciled_invoice_ids[:1] if payment.reconciled_invoice_ids else False
            stamp_by_payment_id[payment.id] = Company.get_stamp_data_uri(
                move=move, tenancy=tenancy, payment=payment,
            )
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'stamp_by_payment_id': stamp_by_payment_id,
        }
