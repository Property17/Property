# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class commission_invoice(models.AbstractModel):

    _name = 'report.property_commission.commission_report_template2'

    def get_datas(self, start_date, end_date):
        """
        This method is used to get data from commission invoice line
        between to two selacted date.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        datas = []
        invoice_obj = self.env['commission.invoice']
        invoice_ids = invoice_obj.search(
            [('date', '<=', end_date),
             ('date', '>=', start_date),
             ('inv', '=', True)])
        for value in invoice_ids:
            datas.append({'property': value.property_id.name,
                          'tenancy': value.tenancy.name,
                          'commission': value.amount_total,
                          'agent': value.agent.name,
                          })
        return datas

    @api.model
    def get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))

        start_date = data['form'].get('start_date', fields.Date.today())
        end_date = data['form'].get(
            'end_date', str(
                datetime.now() + relativedelta
                (months=+1, day=1, days=-1))[:10])

        data_res = self.with_context(
            data['form'].get('used_context', {})).get_datas(
                start_date, end_date)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_datas': data_res,
        }
        docargs['data'].update({'end_date': parser.parse(
            docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
        docargs['data'].update({'start_date': parser.parse(
            docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})

        return docargs
