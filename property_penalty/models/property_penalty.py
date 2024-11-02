# See LICENSE file for full copyright and licensing details

from odoo import models, fields, _
from dateutil.relativedelta import relativedelta


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    penalty = fields.Float(
        string='Penalty (%)')
    penalty_day = fields.Integer(
        string='Penalty Count After Days')


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"
    _order = 'start_date'

    penalty_amount = fields.Float(
        string='Penalty Amount')

    def calculate_penalty(self):
        """
        This Method is used to calculate penalty.
        -----------------------------------------
        @param self: The object pointer
        """
        today_date = fields.Date.context_today(self)
        for tenancy in self:
            if not tenancy.paid:
                ten_date = tenancy.start_date
                if tenancy.tenancy_id.penalty_day != 0:
                    ten_date = ten_date + \
                        relativedelta(
                            days=int(tenancy.tenancy_id.penalty_day))
                if ten_date < today_date:
                    if (today_date - ten_date).days:
                        line_amount_day = (
                            tenancy.tenancy_id.rent
                            * tenancy.tenancy_id.penalty) / 100
                        tenancy.write({'penalty_amount': line_amount_day})
        return True

    def get_invoice_lines(self):
        """TO GET THE INVOICE LINES"""
        inv_lines = super(TenancyRentSchedule, self).get_invoice_lines()
        for tenancy in self:
            inv_line_values = inv_lines[0][2]
            tenancy.calculate_penalty()
            if tenancy.tenancy_id.penalty < 00:
                raise Warning(_(
                    'The Penalty% must be strictly positive.'))
            if tenancy.tenancy_id.penalty_day < 00:
                raise Warning(_('The Penalty Count After Days must be \
                strictly positive.'))
            amt = tenancy.amount + tenancy.penalty_amount
            inv_line_values.update({'price_unit': amt or 0.00})
        return inv_lines
