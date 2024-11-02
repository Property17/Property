# See LICENSE file for full copyright and licensing details

import time
from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class CrmLead(models.Model):
    _inherit = "crm.lead"

    facing = fields.Char(
        string='Facing')
    demand = fields.Boolean(
        string='Is Demand')
    max_price = fields.Float(
        string='Max Price')
    min_price = fields.Float(
        string='Min. Price')
    is_buy = fields.Boolean(
        string='Is Buy',
        default=False)
    is_rent = fields.Boolean(
        string='Is Rent',
        default=False)
    max_bedroom = fields.Integer(
        string='Max Bedroom Require')
    min_bedroom = fields.Integer(
        string='Min. Bedroom Require')
    max_bathroom = fields.Integer(
        string='Max Bathroom Require')
    min_bathroom = fields.Integer(
        string='Min. Bathroom Require')
    furnished = fields.Char(
        string='Furnishing',
        help='Furnishing')
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type',
        help='Property Type')
    email_send = fields.Boolean(
        string='Email Send',
        help="it is checked when email is send")
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')


    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """ Extract data from lead to create a partner.

        :param name : furtur name of the partner
        :param is_company : True if the partner is a company
        :param parent_id : id of the parent partner (False if no parent)

        :return: dictionary of values to give at res_partner.create()
        """
        email_split = tools.email_split(self.email_from)
        res = {
            'name': partner_name,
            'user_id': self.env.context.get('default_user_id') or self.user_id.id,
            'comment': self.description,
            'team_id': self.team_id.id,
            'parent_id': parent_id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': email_split[0] if email_split else False,
            'title': self.title.id,
            'function': self.function,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'website': self.website,
            'is_company': is_company,
            'type': 'contact'
        }
        if self.is_rent:
            res.update({'tenant': True})
            tenant_id = self.env['tenant.partner'].create(res)
            tenant_id.parent_id.write({'tenant': True})
            return tenant_id
        else:
            if self.lang_id:
                res['lang'] = self.lang_id.code
            return super(CrmLead, self)._prepare_customer_values(partner_name=partner_name, is_company=is_company, parent_id=parent_id)



class CrmMakeContract(models.TransientModel):
    _name = "crm.make.contract"
    _description = "Make sales"

    @api.model
    def _selectPartner(self):
        """
        This function gets default value for partner_id field.
        @param self: The object pointer
        @return: default value of partner_id field.
        """
        if self._context is None:
            self._context = {}
        active_id = self._context and self._context.get(
            'active_id', False) or False
        if not active_id:
            return False
        lead_brw = self.env['crm.lead'].browse(active_id)
        lead = lead_brw.read(['partner_id'])[0]
        return lead['partner_id'][0] if lead['partner_id'] else False

    date = fields.Date(
        string='End Date')
    date_start = fields.Date(
        string='Start Date',
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT))
    # partner_id = fields.Many2one(
    #     comodel_name='res.partner',
    #     string='Customer',
    #     default=_selectPartner,
    #     required=True,
    #     domain=[('customer_rank', '>', 0)])
    close = fields.Boolean(
        string='Mark Won',
        default=False,
        help='Check this to close the opportunity after having created the \
        sales order.')

    @api.constrains('date_start', 'date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the end date smaller than
        the start date.
        @param self : object pointer
        """
        for rec in self:
            if rec.date_start and rec.date:
                if rec.date < rec.date_start:
                    raise ValidationError(
                        _('End date should be grater then Start Date !'))

    def makecontract(self):
        """
        This function create Quotation on given case.
        @param self: The object pointer
        @return: Dictionary value of created sales order.
        """
        context = dict(self._context or {})
        context.pop('default_state', False)
        data = context and context.get('active_ids', []) or []
        lead_obj = self.env['crm.lead']
        for make in self:
            # partner = make.partner_id
            new_ids = []
            view_id = self.env.ref(
                'property_management.property_analytic_view_form').id
            for case in lead_obj.browse(data):
                # if not partner and case.partner_id:
                #     partner = case.partner_id
                # case._prepare_customer_values(
                tenant_id = case._prepare_customer_values(case.contact_name, is_company=False)
                print("++++++++++++++++++++++++++++++++++++++++++")
                print(tenant_id)
                case.partner_id = tenant_id['parent_id'],
                vals = {
                    'name': case.name,
                    'partner_id': tenant_id.get('parent_id'),
                    'property_id': case.property_id.id or False,
                    'plan_id':self.env.ref('analytic.analytic_plan_projects').id,
                    # 'tenant_id': tenant_id.id,
                    'company_id': self.env.company.id,
                    'date_start': make.date_start or False,
                    'date': make.date or False,
                    # 'type': 'contract',
                    'is_property': True,
                    'rent': case.property_id.ground_rent,
                }
                new_id = self.env['account.analytic.account'].create(vals)

                case.write({
                    'description': 'account.analytic.account,%s' % new_id})
                new_ids.append(new_id.id)
                message = _(
                    "Opportunity has been <b>converted</b> to the \
                    Contract <em>%s</em>.") % (new_id.name)
                case.message_post(body=message)
            if make.close:
                case.action_set_won()
            if not new_ids:
                return {'type': 'ir.actions.act_window_close'}
            value = {
                'domain': str([('id', 'in', new_ids)]),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.analytic.account',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'name': _('Contract'),
                'res_id': new_ids
            }

            if len(new_ids) <= 1:
                value.update(
                    {'view_mode': 'form', 'res_id': new_ids and new_ids[0]})
            return value
