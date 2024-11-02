# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SafetyCertificateReport(models.TransientModel):
    _name = 'safety.certificate.report'
    _description = 'Safety Certificate Report'

    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date',
        required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Exiration date.
        @param self : object pointer
        """
        for ver in self:
            if ver.start_date and ver.end_date and \
                    ver.end_date < ver.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start Date!'))

    def open_certificate_expiry_tree(self):
        """
        This method is used to open record in tree view between selected dates
        @param self : object pointer
        """
        wiz_form_id = self.env.ref(
            'property_management.property_certificate_view_tree').id
        certificate_obj = self.env['property.safety.certificate']
        for data1 in self:
            data = data1.read([])[0]
            start_date = data['start_date']
            end_date = data['end_date']
            certificate_ids = certificate_obj.search(
                [('expiry_date', '>=', start_date),
                 ('expiry_date', '<=', end_date)])
        return {'name': _('Safety Certificate Expiry'),
                'view_type': 'form',
                'view_id': wiz_form_id,
                'view_mode': 'tree',
                'res_model': 'property.safety.certificate',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': self._context,
                'domain': [('id', 'in', certificate_ids.ids)],
                }

    def print_report(self):
        return self.env.ref(
            'property_management.action_report_safety_certificate'
        ).report_action(
            [], data={
                'ids': self.ids,
                'model': 'account.asset',
                'form': self.read(['start_date', 'end_date'])[0]
            })
