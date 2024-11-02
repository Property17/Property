# See LICENSE file for full copyright and licensing details
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

DEFAULT_FACTURX_DATE_FORMAT = '%Y-%m-%d'

class document_expiry(models.AbstractModel):
    _name = 'report.property_management.report_document_expiry'
    _description = 'Document Expiry Report'

    def date_format(self, date):
        user_lang = self.env.user.lang
        lang = self.env['res.lang'].search(
            [('code', '=', user_lang)])
        if date:
            final_from_date = date.strftime(lang.date_format)
        return final_from_date

    def get_details(self, start_date, end_date):
        data_1 = []
        certificate_obj = self.env["property.attachment"]
        certificate_ids = certificate_obj.search(
            [('expiry_date', '>=', start_date),
             ('expiry_date', '<=', end_date)])
        for data in certificate_ids:
            data_1.append({
                'name': data.name,
                'property_id': data.property_id.name,
                'expiry_date': self.date_format(data.expiry_date),
            })
        return data_1

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.asset'].browse(docids)
        start_date_obj = datetime.strptime(
            data['form'].get('start_date'), '%Y-%m-%d')
        start_date_report = self.date_format(start_date_obj)
        end_date_obj = datetime.strptime(
            data['form'].get('end_date'), '%Y-%m-%d')
        end_date_report = self.date_format(end_date_obj)
        start_date = data['form'].get('start_date', fields.Date.today())
        end_date = data['form'].get(
            'end_date', str(datetime.now() + relativedelta(
                months=+1, day=1, days=-1))[:10])
        detail_res = self.with_context(
            data['form'].get('used_context', {})).get_details(
                start_date, end_date)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.asset',
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_details': detail_res,
        }
        docargs['data'].update({
            'end_date': end_date_report,
            'start_date': start_date_report})
        return docargs
