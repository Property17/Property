# See LICENSE file for full copyright and licensing details
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools.misc import formatLang, get_lang


class IncomeExpenditure(models.AbstractModel):
    _name = 'report.property_management.report_income_expenditure'
    _description = 'Income Expenditure Report'

    def get_details(self, start_date, end_date):
        report_rec = []
        total_in = 0.00
        total_ex = 0.00
        total_gr = 0.00
        lang = get_lang(self.env).code
        currency = False
        property_obj = self.env['account.asset']
        income_obj = self.env["tenancy.rent.schedule"]
        properties = property_obj.search([])
        for property in properties:
            currency = property.currency_id
            tenancies = income_obj.search(
                [('start_date', '>=', start_date),
                    ('start_date', '<=', end_date),
                    ('tenancy_id', 'in', property.tenancy_property_ids.ids)])
            total_income = 0.00
            total_expence = 0.00
            if tenancies:
                for income_id in tenancies:
                    total_income += income_id.amount

                report_rec.append({
                    'property': property.name,
                    'total_income': total_income,
                    'total_expence': total_expence,
                    'currency_id': property.currency_id,
                    'total_in': '',
                    'total_ex': '',
                    'total_gr': '',
                })
        total_gr = total_in - total_ex
        if total_in and total_ex and total_gr:
            report_rec.append({
                'property': '',
                'total_income': '',
                'total_expence': '',
                'currency_id': property.currency_id,
                'total_in': formatLang(lang, total_in, currency_obj=currency),
                'total_ex': formatLang(lang, total_ex, currency_obj=currency),
                'total_gr': formatLang(lang, total_gr, currency_obj=currency),
            })
        return report_rec

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
            'end_date': self.date_format(docargs.get('data').get('end_date')),
            'start_date': self.date_format(docargs.get('data').get(
                'start_date'))})
        return docargs
