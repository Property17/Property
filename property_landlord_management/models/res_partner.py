# See LICENSE file for full copyright and licensing details
from odoo import _, fields, models, api
from odoo.exceptions import UserError


class LandlordPartner(models.Model):
    _name = "landlord.partner"
    _description = 'Landlord Partner'
    _inherits = {'res.partner': 'parent_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']


    doc_name = fields.Char(
        string='Filename')
    id_attachment = fields.Binary(
        string='Identity Proof')
    owner_tenancy_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='property_owner_id',
        string='Landlord Details',
        help='Landlord Details')
    parent_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        index=True,
        ondelete='cascade')

    @api.model
    def create(self, vals):
        """
        This Method is used to override orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        property_user = False
        res = super(LandlordPartner, self).create(vals)
        if self._context.get('is_owner'):
            password = self.env['res.company'].browse(
                vals.get('company_id', False)).default_password
            if not password:
                password = ''
            create_user = self.env['res.users'].create({
                'login': vals.get('email'),
                'name': vals.get('name'),
                'password': password,
                'partner_id': res.parent_id.id,
            })
            if res.customer_rank > 0:
                property_user = \
                    self.env.ref('property_management.group_property_user')
            if res.agent:
                property_user = \
                    self.env.ref('property_management.group_property_agent')
            if res.is_owner:
                property_user = \
                    self.env.ref('property_management.group_property_owner')
            if property_user:
                property_user.write({'users': [(4, create_user.id)]})
        return res

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        running_landlord = self.env['account.analytic.account'].search(
            [('property_owner_id', '=', self.id)])
        for landlord_tenancy_rec in running_landlord:
            if landlord_tenancy_rec:
                raise UserError(
                    _('You cannot delete landlord while there are active '
                        'landlord tenancy.'))
        return super(LandlordPartner, self).unlink()

    def _message_get_suggested_recipients(self):
        recipients = super(
            LandlordPartner, self)._message_get_suggested_recipients()
        for partner in self:
            if partner.parent_id:
                partner._message_add_suggested_recipient(
                    recipients, partner=partner.parent_id,
                    reason=_('Partner ''Profile'))
        return recipients


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_owner = fields.Boolean(
        string='Is a Owner',
        help="Check this box if this contact is a landlord(owner).")
