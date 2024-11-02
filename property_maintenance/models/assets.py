# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _


class AccountAsset(models.Model):
    _inherit = 'account.asset'
    _description = 'Asset'

    def _compute_request_count(self):
        for asset in self:
            asset.maint_request = len(asset.maintenance_ids.ids)

    maint_request = fields.Integer(
        string='Request',
        compute='_compute_request_count',
        help='Only shows new request maintenance for this property')
    maintenance_ids = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='property_id',
        string='Maintenance Request',
        help='Its shows over all maintenance for this property')
    maint_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Maintenance Account')

    def open_maintenance(self):
        ctx = dict(self._context or {})
        ctx.update({'default_property_id': self.id})
        return {
            'name': _('Maintenance Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'maintenance.request',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('property_id', '=', self.id)],
            'context': ctx,
        }

    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent',
                 'maintenance_ids', 'maintenance_ids.cost')
    def roi_calculation(self):
        """
        This Method is used to Calculate ROI(Return On Investment).
        @param self: The object pointer
        @return: Calculated Return On Investment.
        """
        cost_of_investment = 0
        gain_from_investment = 0
        total = 0
        for prop_rec in self:
            if prop_rec.maintenance_ids and prop_rec.maintenance_ids.ids:
                cost_of_investment = sum(
                    [maintenance.cost for maintenance in
                     prop_rec.maintenance_ids])
            if prop_rec.tenancy_property_ids and \
                    prop_rec.tenancy_property_ids.ids:
                gain_from_investment = sum(
                    [gain.rent for gain in prop_rec.tenancy_property_ids])
            if (cost_of_investment != 0 and gain_from_investment != 0
                    and cost_of_investment != gain_from_investment):
                total = (gain_from_investment - cost_of_investment) / \
                    cost_of_investment
            prop_rec.roi = total
