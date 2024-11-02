# See LICENSE file for full copyright and licensing details
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools import ustr


class TenancyDetailByTenant(models.AbstractModel):
    _name = 'report.property_management.report_tenancy_by_tenant'
    _description = 'Tenancy By Tenant'

    def get_details(self, start_date, end_date, tenant_id):
        data_1 = []
        tenancy_obj = self.env["account.analytic.account"]
        tenancy_ids = tenancy_obj.search([
            ('tenant_id', '=', tenant_id[0]),
            ('date_start', '>=', start_date),
            ('date_start', '<=', end_date),
            ('resident_type', '=', 'tenant_tenancy')])
        for data in tenancy_ids:
            if data.currency_id:
                cur = data.currency_id.symbol
            user_lang = self.env.user.lang
            lang = self.env['res.lang'].search(
                [('code', '=', user_lang)])
            if data.date_start:
                date_start = data.date_start.strftime(lang.date_format)
            if data.date:
                date = data.date.strftime(lang.date_format)
            data_1.append({
                'property_id': data.property_id.name,
                'date_start': date_start,
                'date': date,
                'rent': cur + ustr(data.rent),
                'deposit': cur + ustr(data.deposit),
                'rent_type_id': data.rent_type_id.name,
                'rent_type_month': data.rent_type_id.renttype,
                'state': data.state
            })
        return data_1

    def date_format(self, date):
        from_date = datetime.strptime(date, '%Y-%m-%d')
        user_lang = self.env.user.lang
        lang = self.env['res.lang'].search(
            [('code', '=', user_lang)])
        if from_date:
            final_from_date = from_date.strftime(lang.date_format)
        return final_from_date

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.asset'].browse(docids)
        start_date = data['form'].get('start_date', fields.Date.today())
        end_date = data['form'].get(
            'end_date', str(datetime.now() + relativedelta(
                months=+1, day=1, days=-1))[:10])
        tenant_id = data['form'].get('tenant_id')

        detail_res = self.with_context(data['form'].get(
            'used_context', {})).get_details(
            start_date, end_date, tenant_id)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.asset',
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_details': detail_res,
        }
        docargs['data'].update({
            'end_date': self.date_format(docargs.get('data').get('end_date')),
            'start_date': self.date_format(docargs.get('data').get(
                'start_date'))})
        return docargs
