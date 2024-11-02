# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class CommissionReport(models.TransientModel):
    _name = 'commission.report'

    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date',
        required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date
        smaller than the Expiration date.
        -------------------------------------------------------
        @param self : object pointer
        """
        for ver in self:
            if ver.start_date and ver.end_date:
                dt_from = datetime.strptime(
                    ver.start_date, DEFAULT_SERVER_DATE_FORMAT)
                dt_to = datetime.strptime(
                    ver.end_date, DEFAULT_SERVER_DATE_FORMAT)
                if dt_to < dt_from:
                    raise ValidationError(
                        'End date should be greater than Start date.')

    def print_report(self):
        if self._context is None:
            self._context = {}
        data = {
            'ids': self.ids,
            'model': 'commission.report',
            'form': self.read(['start_date', 'end_date'])[0]
        }
        return self.env.ref(
            'property_commission.commission_for_invoice_report').report_action(
            [], data=data)
