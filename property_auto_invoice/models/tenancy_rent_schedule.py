# See LICENSE file for full copyright and licensing details

from odoo import fields, models, _


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"

    def create_auto_invoice_rent_schedule(self):
        property_inv_type_param = self.env['ir.config_parameter'].sudo().get_param(
            'property_auto_invoice.inv_type')
        if property_inv_type_param == 'automatic':
            today = fields.Date.context_today(self)
            rent_ids = self.env['tenancy.rent.schedule'].search([('paid', '=', False), ('start_date', '=', today)])
            for rent_schedule in rent_ids.filtered(lambda l: l.tenancy_id.state == 'open'):
                if rent_schedule:
                    inv_obj = self.env['account.move'].search(
                        [('date', '=', today), ('new_tenancy_id', '=', rent_schedule.tenancy_id.id)])
                    if not inv_obj:
                        rent_schedule.create_invoice()
