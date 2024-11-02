# See LICENSE file for full copyright and licensing details


from odoo.exceptions import ValidationError
from odoo import _, api, fields, models


class WizardRenewTenancy(models.TransientModel):
    _name = 'renew.tenancy'
    _description = 'Renew Tenancy'

    start_date = fields.Date(
        string='Start Date')
    end_date = fields.Date(
        string='End Date')
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type',
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

    def renew_contract(self):
        """
        This Button Method is used to Renew Tenancy.
        @param self: The object pointer
        @return: Dictionary of values.
        """
        context = dict(self._context) or {}
        modid = self.env.ref(
            'property_management.property_analytic_view_form').id
        if context.get('active_ids', []):
            for rec in self:
                start_d = rec.start_date
                end_d = rec.end_date
                if start_d > end_d:
                    raise ValidationError(
                        _('Please Insert End Date Greater Than Start Date!'))
                act_prop = self.env['account.analytic.account'].browse(
                    context['active_ids'])
                act_prop.write({
                    'date_start': rec.start_date,
                    'date': rec.end_date,
                    'rent_type_id':
                    rec.rent_type_id and rec.rent_type_id.id or False,
                    'state': 'draft',
                    'rent_entry_chck': False,
                })
        return {
            'view_mode': 'form',
            'view_id': modid,
            'view_type': 'form',
            'res_model': 'account.analytic.account',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': context['active_ids'][0],
        }
