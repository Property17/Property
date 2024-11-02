from odoo import api, fields, models, _
from odoo.exceptions import UserError , ValidationError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    property_user = fields.Selection([('owner', 'Owner'),
                              ('property_manager', 'Property Manager')],
                             string='Property User')
    property_rent_sale = fields.Selection([('rent', 'Rent'),
                              ('sale', 'Sale')],
                             string='Property For')
    type_id = fields.Many2one('property.type','Property Type')

    def register_authorized_user(self):
        user_obj = self.env['res.users']
        company_obj = self.env['res.company']
        existing_user = user_obj.search([('login', '=', self.email_from)])
        if not self.contact_name and not self.email_from:
                raise ValidationError(_('Please enter Contact name and email id.'))
        elif existing_user:
            raise ValidationError(_('User Already Exists For This Email Id'))
        else:
            values = self._prepare_customer_values(self.contact_name, True, False)
#             groups = [self.env.ref('base.group_portal').id]
            groups = []
            if self.property_user == 'owner':
                groups.append(self.env.ref('property_management.group_property_owner').id)
                values.update({'is_owner': True})
            if self.property_user == '':
                values.update({'agent': True})
                groups.append(self.env.ref('property_management.group_property_agent').id)
            values.update({'company_id': self.company_id and self.company_id.id,
                           'groups_id': [(6, 0, groups)],
                           'login': self.email_from,
            })
            values.pop('user_id', '')
            user = user_obj.sudo().create(values)
            if user:
                self.convert_opportunity(user.partner_id)
                self.action_set_won()
                if self.property_user == 'owner':
                    self.env['landlord.partner'].create({'parent_id': user.partner_id.id,})
                return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'res.users',
                        'view_mode': 'form',
                        'view_id': self.env.ref('base.view_users_form').id,
                        'res_id': user.id,
                        'target': 'current',
                        }

