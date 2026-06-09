# -*- coding: utf-8 -*-

from odoo import api, models


def _include_stamp(env):
    """Stamp is shown on portal receipt PDFs only, not backend accounting prints."""
    return bool(env.context.get('portal_receipt_stamp'))


def _stamp_data_uri(env, move=None, tenancy=None, payment=None):
    """Resolve company stamp as a base64 data URI for QWeb PDFs."""
    Company = env['res.company']
    if hasattr(Company, 'get_stamp_data_uri'):
        return Company.get_stamp_data_uri(move=move, tenancy=tenancy, payment=payment)
    company = (payment and payment.company_id or move and move.company_id or env.company).sudo()
    stamp = getattr(company, 'stamp', False)
    if stamp:
        from odoo.tools.image import image_data_uri
        return image_data_uri(stamp)
    return False


def _move_and_tenancy_from_payment(env, payment):
    move = payment.mm_move_id or payment.mm_invoice_id
    if not move and payment.ref:
        move = env['account.move'].search([
            ('name', '=', payment.ref),
            ('company_id', '=', payment.company_id.id),
        ], limit=1)
    if not move and payment.reconciled_invoice_ids:
        move = payment.reconciled_invoice_ids[:1]
    if not move and payment.property_id and payment.partner_id:
        move = env['account.move'].search([
            ('partner_id', '=', payment.partner_id.id),
            ('property_id', '=', payment.property_id.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ], limit=1, order='invoice_date desc, id desc')
    tenancy = payment.tenancy_id
    if not tenancy and move:
        tenancy = getattr(move, 'tenancy_id', False) or getattr(move, 'new_tenancy_id', False)
    if not tenancy and move:
        schedule = env['tenancy.rent.schedule'].search([('invoice_id', '=', move.id)], limit=1)
        tenancy = schedule.tenancy_id if schedule else False
    return move, tenancy


def _tenancy_from_move(env, move):
    tenancy = getattr(move, 'tenancy_id', False) or getattr(move, 'new_tenancy_id', False)
    if not tenancy:
        schedule = env['tenancy.rent.schedule'].search([('invoice_id', '=', move.id)], limit=1)
        tenancy = schedule.tenancy_id if schedule else False
    return tenancy


class ReportAccountPaymentReceipt(models.AbstractModel):
    _name = 'report.account.report_payment_receipt'
    _description = 'Payment receipt with company stamp'

    @api.model
    def _get_report_values(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids).sudo()
        stamp_by_payment_id = {
            payment.id: False for payment in payments
        }
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'stamp_by_payment_id': stamp_by_payment_id,
        }


class ReportPaymentDepositeDocument(models.AbstractModel):
    _name = 'report.pyment_report.report_payment_deposite_document'
    _description = 'Deposit receipt with company stamp'

    @api.model
    def _get_report_values(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids).sudo()
        stamp_by_payment_id = {
            payment.id: False for payment in payments
        }
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'stamp_by_payment_id': stamp_by_payment_id,
        }


class ReportPaymentDepositePortal(models.AbstractModel):
    _name = 'report.pyment_report.report_payment_deposite_document_portal'
    _description = 'Deposit receipt (portal) with company stamp'

    @api.model
    def _get_report_values(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids).sudo()
        stamp_by_payment_id = {}
        for payment in payments:
            move, tenancy = _move_and_tenancy_from_payment(self.env, payment)
            stamp_by_payment_id[payment.id] = _stamp_data_uri(
                self.env, move=move, tenancy=tenancy, payment=payment,
            )
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'stamp_by_payment_id': stamp_by_payment_id,
        }


class ReportMultiInvoice(models.AbstractModel):
    _inherit = 'report.pyment_report.mm_multi_invoice_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data)
        for move, doc in zip(self.env['account.move'].browse(docids), res.get('docs') or []):
            if _include_stamp(self.env):
                tenancy = _tenancy_from_move(self.env, move)
                doc['stamp_data_uri'] = _stamp_data_uri(
                    self.env, move=move, tenancy=tenancy,
                )
            else:
                doc['stamp_data_uri'] = False
        return res


class ReportMultiDeposite(models.AbstractModel):
    _inherit = 'report.pyment_report.mm_multi_deposite_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data)
        for doc in res.get('docs') or []:
            doc['stamp_data_uri'] = False
        return res
