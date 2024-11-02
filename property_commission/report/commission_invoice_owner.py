# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class CommissionInvoiceOwner(models.AbstractModel):
    _name = 'report.property_commission.commission_invoice_owner'

    def get_data(self, start_date, end_date, company_id):
        """
        This method is used to get data from commission invoice line
        between to two selacted date and companny
        ------------------------------------------------------------
        @param self: The object pointer
        """
        invoice_ids = []
        comm_obj = self.env['commission.invoice.line']
        for line in comm_obj.search(
            [('inv', '=', True),
             ('date', '>=', start_date),
             ('date', '<=', end_date),
             ('commission_id.company_id', '=', company_id)]):
            for invoice in line.invc_id:
                invoice_ids.append(invoice)
        return invoice_ids

    @api.model
    def render_html(self, docids, data=None,):
        i = self._context.get('data')
        self.model = self.env.context.get('active_model')
        if i:
            start_date = i['form'].get('start_date', fields.Date.today())
            end_date = i['form'].get(
                'end_date', str(datetime.now() + relativedelta(
                    months=+1, day=1, days=-1))[:10])
            company_id = i['form'].get('company_id')[1]

            data_res = self.with_context(
                i['form'].get('used_context', {})).get_data(
                    start_date, end_date, company_id)
            aa = self.get_data(start_date, end_date, company_id)
            docargs = {
                'doc_ids': docids,
                'doc_model': self.model,
                'data': i['form'],
                'docs': aa,
                'time': time,
                'get_data': data_res,
            }
            docargs['data'].update({'end_date': parser.parse(
                docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
            docargs['data'].update({'start_date': parser.parse(
                docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})

            return self.env['report'].render(
                'property_commission.commission_invoice_owner', docargs)

        else:
            start_date = data['form'].get('start_date', fields.Date.today())
            end_date = data['form'].get(
                'end_date', str(datetime.now() + relativedelta(
                    months=+1, day=1, days=-1))[:10])
            company_id = data['form'].get('company_id')[1]
            data_res = self.with_context(
                data['form'].get('used_context', {})).get_data(
                    start_date, end_date, company_id)
            aa = self.get_data(start_date, end_date, company_id)

            docargs = {
                'doc_ids': docids,
                'doc_model': self.model,
                'data': data['form'],
                'docs': aa,
                'time': time,
                'get_data': data_res,
            }
            docargs['data'].update({'end_date': parser.parse(
                docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
            docargs['data'].update({'start_date': parser.parse(
                docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})

            return self.env['report'].render(
                'property_commission.commission_invoice_owner', docargs)
