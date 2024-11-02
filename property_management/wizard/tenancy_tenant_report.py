# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TenancyTenantReport(models.TransientModel):
    _name = 'tenancy.tenant.report'
    _description = 'Tenancy Tenant Report'

    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date',
        required=True)
    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Tenant',
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

    def open_tanancy_tenant_gantt_view(self):
        """
        This method is used to open record in gantt view between selected dates
        @param self : object pointer
        """
        wiz_form_id = self.env.ref(
            'property_management.view_analytic_gantt').id
        analytic_obj = self.env["account.analytic.account"]
        for data_rec in self:
            data = data_rec.read([])[0]
            tenancy_ids = analytic_obj.search(
                [('tenant_id', '=', data['tenant_id'][0]),
                 ('date_start', '>=', data['start_date']),
                 ('date_start', '<=', data['end_date'])])
            return {
                'view_type': 'form',
                'view_id': wiz_form_id,
                'view_mode': 'gantt',
                'res_model': 'account.analytic.account',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': self._context,
                'domain': [('id', 'in', tenancy_ids.ids)],
            }

    def open_tanancy_tenant_tree_view(self):
        """
        This method is used to open record in tree view between selected dates
        @param self : object pointer
        """
        wiz_form_id = self.env.ref(
            'property_management.property_analytic_report_view_tree').id
        analytic_obj = self.env['account.analytic.account']
        for data_rec in self:
            data = data_rec.read([])[0]
            tenancy_ids = analytic_obj.search(
                [('tenant_id', '=', data['tenant_id'][0]),
                 ('date_start', '>=', data['start_date']),
                 ('date_start', '<=', data['end_date'])])
            return {'name': _('Tenancy Report By Tenant'),
                    'view_type': 'form',
                    'view_id': wiz_form_id,
                    'view_mode': 'tree',
                    'res_model': 'account.analytic.account',
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': self._context,
                    'domain': [('id', 'in', tenancy_ids.ids)],
                    }

    def print_report(self):
        partner_obj = self.env['tenant.partner']
        for data_rec in self:
            data = data_rec.read([])[0]
            partner_rec = partner_obj.browse(data['tenant_id'][0])
            data.update({'tenant_name': partner_rec.name})
        return self.env.ref(
            'property_management.action_report_tenancy_by_tenant'
        ).report_action(
            [], data={
                'ids': self.ids,
                'model': 'tenant.partner',
                'form': data
            })
