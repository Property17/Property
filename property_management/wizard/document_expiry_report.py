# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DocumentExpiryReport(models.TransientModel):
    _name = 'document.expiry.report'
    _description = 'Document Expiry Report'

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

    def open_document_expiry_tree(self):
        """
        This method is used to open record in tree view between selected dates
        @param self : object pointer
        """
        wiz_form_id = self.env.ref(
            'property_management.property_attachment_view_tree').id
        attachment_obj = self.env["property.attachment"]
        for data1 in self:
            data = data1.read([])[0]
            certificate_ids = attachment_obj.search(
                [('expiry_date', '>=', data['start_date']),
                 ('expiry_date', '<=', data['end_date'])])
        return {'name': _('Document Expiry Report'),
                'view_type': 'form',
                'view_id': wiz_form_id,
                'view_mode': 'tree',
                'res_model': 'property.attachment',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('id', 'in', certificate_ids.ids)],
                }

    def print_report(self):
        datas = {
            'ids': self.ids,
            'model': 'account.asset',
            'form': self.sudo().read(['start_date', 'end_date'])[0]
        }
        return self.env.ref(
            'property_management.action_report_document_expiry').report_action(
            self, data=datas)
