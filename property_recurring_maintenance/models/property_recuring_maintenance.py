# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecurringMaintenanceType(models.Model):
    _name = 'recurring.maintenance.type'
    _description = 'Recurring Maintenance Type'

    name = fields.Char(
        string='Maintenance Type',
        size=50,
        required=True,
        help='Name of Maintenance Type Example Maintain Garden, Maintain \
              Swimming pool')
    cost = fields.Float(
        string='Maintenance Cost',
        help='Cost of maintenance type',)
    maintenance_team_id = fields.Many2one(
        comodel_name='maintenance.team',
        string='Maintenance Team',
        help='Select team who manage this recurring maintenance.')

    @api.constrains('cost')
    def check_negative_value(self):
        for property in self:
            if property.cost < 0:
                raise ValidationError(
                    _('You can not enter negative Maintenance Cost.'))


class RecurringMaintenanceLine(models.Model):
    _name = 'recurring.maintenance.line'
    _description = 'Recurring Maintenance Line'

    date = fields.Date(
        string='Expiration Date',
        help="Tenancy contract end date.")
    maintenance_type_ids = fields.Many2many(
        comodel_name='recurring.maintenance.type',
        relation='recurring_maintenance_type_rel',
        column1='recurring_line_id',
        column2='maintenance_typ_id',
        string='Maintenance Types')


class MaintenanceCost(models.Model):
    _name = 'maintenance.cost'
    _description = 'Maintenance Cost'

    maintenance_type = fields.Many2one(
        comodel_name='recurring.maintenance.type',
        string='Maintenance Type',
        help='Recurring maintenance type')
    cost = fields.Monetary(
        string='Maintenance Cost',
        currency_field='currency_id',
        help='recurring maintenance cost')
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', required=True, default=lambda self: self.env.company.currency_id)

    @api.constrains('cost')
    def check_negative_value(self):
        for property in self:
            if property.cost < 0:
                raise ValidationError(
                    _('You can not enter negative Maintenance Cost.'))

    @api.onchange('maintenance_type')
    def onchange_property_id(self):
        """
        This Method is used to set maintenance type related fields value,
        on change of property.
        --------------------------------------------------------------------
        @param self: The object pointer
        """
        for data in self:
            if data.maintenance_type:
                data.cost = data.maintenance_type.cost or 0.00


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.depends('maintenance_cost_ids.cost')
    def _compute_total_cost_maint(self):
        """
        This method is used to calculate total maintenance
        boolean field accordingly to current Tenancy.
        -------------------------------------------------------------
        @param self: The object pointer
        """
        for maintenance in self:
            maintenance.maintenance_cost = False
            maintenance.maintenance_cost = \
                sum(recurring.cost for recurring in maintenance.maintenance_cost_ids) or 0.0

    maintenance_cost_ids = fields.One2many(
        comodel_name='maintenance.cost',
        inverse_name='tenancy',
        string='cost',
        help='it shows all recurring maintenance assigned to this tenancy')

    maintenance_cost = fields.Monetary(
        string='Maintenance Cost',
        store=True,
        currency_field='currency_id',
        compute='_compute_total_cost_maint',
        help="Its shows overall cost of recurring maintenance")


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"

    def get_invoice_lines(self):
        """
        TO GET THE INVOICE LINES
        """
        inv_lines = super(TenancyRentSchedule, self).get_invoice_lines()
        for rec in self:
            if rec.tenancy_id.maintenance_cost:
                inv_line_main = {
                    # 'origin': 'tenancy.rent.schedule',
                    'name': 'Maintenance cost',
                    'price_unit': self.tenancy_id.maintenance_cost or 0.00,
                    'quantity': 1,
                    'account_id': self.tenancy_id.property_id.
                    income_acc_id.id or False,
                    'analytic_account_id': self.tenancy_id.id or False,
                }
                if rec.tenancy_id.rent_type_id.renttype == 'Monthly':
                    m = rec.tenancy_id.maintenance_cost * \
                        float(rec.tenancy_id.rent_type_id.name)
                    inv_line_main.update({'price_unit': m})
                if rec.tenancy_id.rent_type_id.renttype == 'Yearly':
                    y = rec.tenancy_id.maintenance_cost * \
                        float(rec.tenancy_id.rent_type_id.name) * 12
                    inv_line_main.update({'price_unit': y})
                inv_lines.append((0, 0, inv_line_main))
        return inv_lines
