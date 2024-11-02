# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    property_id = fields.Many2one(
        string="Property Name",
        comodel_name="account.asset",
        help="Name of the property.")
    cost = fields.Float(
        string='Cost',
        default=0.0,
        help='Cost for over all maintenance')
    done = fields.Boolean(
        string='Stage Done')
    renters_fault = fields.Boolean(
        string='Renters Fault',
        default=False,
        copy=True,
        help='If this maintenance are fault by tenant than its true')
    invoice_id = fields.Many2one(
        comodel_name='account.move', copy=False,
        string='Invoice')
    date_invoice = fields.Date(
        related="invoice_id.invoice_date",
        store=True,
        string='Invoice Date')
    invoice_check = fields.Boolean(
        string='Already Created', copy=False,
        default=False)
    account_id = fields.Many2one(
        comodel_name='account.account',
        store=True,
        string='Maintenance Account')
    city = fields.Char(
        related='property_id.city',
        string='City',
        help='Enter the City')
    street = fields.Char(
        related='property_id.street',
        string='Street',
        help='Property street name')
    street2 = fields.Char(
        related='property_id.street2',
        string='Street2',
        help='Property street2 name')
    township = fields.Char(
        related='property_id.township',
        string='Township',
        help='Property Township name')
    zip = fields.Char(
        related='property_id.zip',
        string='Zip',
        size=24,
        change_default=True,
        help='Property zip code')
    state_id = fields.Many2one(
        related='property_id.state_id',
        comodel_name='res.country.state',
        string='State',
        ondelete='restrict',
        help='Property state name')
    country_id = fields.Many2one(
        related='property_id.country_id',
        comodel_name='res.country',
        string='Country',
        ondelete='restrict',
        help='Property country name')
    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Tenant')
    is_in_progress = fields.Boolean(
        string='In Progress',
        default=False)

    @api.constrains('request_date', 'schedule_date','cost')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Exiration date.
        @param self : object pointer
        """
        for maintenance in self:
            if maintenance.request_date and maintenance.schedule_date and maintenance.schedule_date.date() < maintenance.request_date:
                raise ValidationError(_(
                    'Schedule Date should be greater than Requested Date!'))
            if maintenance.cost < 0:
                raise ValidationError(
                    _('Total Maintenance cost must be grater than zero.'))

    @api.model
    def create(self, vals):
        request = super(MaintenanceRequest, self).create(vals)
        if vals.get('property_id') and not vals.get('tenant_id'):
            tenant_id = self.env['account.analytic.account'].search(
                [('property_id', '=', vals.get('property_id')),
                 ('resident_type', '=', 'tenant_tenancy'),
                 ('state', 'not in', ['close', 'cancelled'])], limit=1).tenant_id
            if tenant_id:
                vals.update({'tenant_id': tenant_id.id})
        return request

    def open_google_map(self):
        """
        This Button method is used to open a URL
        according fields values.
        @param self: The object pointer
        """
        url = "http://maps.google.com/maps?oi=map&q="
        if self.property_id:
            for line in self.property_id:
                if line.name:
                    street_s = re.sub(r'[^\w]', ' ', line.name)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.street:
                    street_s = re.sub(r'[^\w]', ' ', line.street)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.street2:
                    street_s = re.sub(r'[^\w]', ' ', line.street2)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.township:
                    street_s = re.sub(r'[^\w]', ' ', line.township)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.city:
                    street_s = re.sub(r'[^\w]', ' ', line.city)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.state_id:
                    street_s = re.sub(r'[^\w]', ' ', line.state_id.name)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.country_id:
                    street_s = re.sub(r'[^\w]', ' ', line.country_id.name)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.zip:
                    url += line.zip
            return {
                'name': 'Go to website',
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'current',
                'url': url
            }

    @api.onchange('property_id')
    def state_details_change(self):
        for line in self:
            if line.property_id:
                line.tenant_id = self.env['account.analytic.account'].search(
                    [('property_id', '=', line.property_id.id),
                     ('is_property', '=', True),
                     ('state', '!=', 'close'),
                     ('state', '!=', 'cancelled')], limit=1).tenant_id
            if line.property_id and line.property_id.maint_account_id:
                line.account_id = line.property_id.maint_account_id.id


    def write(self, vals):
        res = super(MaintenanceRequest, self).write(vals)
        if self.stage_id.is_in_progress and 'stage_id' in vals:
            self.write({'is_in_progress': True})
            for maintenance in self:
                if maintenance.renters_fault:
                    template_id = \
                        self.env.ref(
                            'property_maintenance.'
                            'mail_maintenance_tenant_inprogress_template')
                    tenant_email = maintenance.tenant_id.email
                    template_id.write({
                        'email_to':tenant_email
                    })
                else:
                    template_id = self.env.ref(
                        'property_maintenance.'
                        'mail_maintenance_manager_inprogress_template')
                    manager_email = \
                        maintenance.property_id.property_manager.email
                    template_id.write({
                        'email_to':manager_email
                    })
            template_id.send_mail(maintenance.id, force_send=True)
        if not self.stage_id.is_in_progress and 'stage_id' in vals: 
            self.write({'is_in_progress': False})
        if self.stage_id.done and 'stage_id' in vals:
            self.write({'done': True})
            for maintenance in self:
                if maintenance.renters_fault:
                    template_id = self.env.ref(
                        'property_maintenance.'
                        'mail_maintenance_tenant_done_template')
                    tenant_email = maintenance.tenant_id.email
                    template_id.write({
                        'email_to':tenant_email
                    })
                else:
                    template_id = self.env.ref(
                        'property_maintenance.'
                        'mail_maintenance_manager_done_template')
                    manager_email = \
                        maintenance.property_id.property_manager.email
                    template_id.write({
                        'email_to':manager_email
                    })
            template_id.send_mail(maintenance.id, force_send=True)
        return res

    def create_invoice(self):
        """
        This Method is used to create invoice from maintenance record.
        --------------------------------------------------------------
        @param self: The object pointer
        """
        inv_line_values = []
        for maintenance in self:
            if not maintenance.property_id.id:
                raise ValidationError(_("Please Select Property"))
            tenancy_ids = self.env['account.analytic.account'].search(
                [('property_id', '=', maintenance.property_id.id), (
                    'state', '!=', 'close')])
            if len(tenancy_ids.ids) == 0:
                inv_line_values.append((0, 0, {
                    'name': 'Maintenance For ' + maintenance.name or "",
                    'ref': 'Maintenance Request',
                    'quantity': 1,
                    'account_id': maintenance.account_id.id or False,
                    'price_unit': maintenance.cost or 0.00,
                }))
                inv_values = {
                    'invoice_origin': 'Maintenance Request' or "",
                    'move_type': 'out_invoice',
                    'partner_id': maintenance.property_id.company_id.partner_id.id or False,
                    'property_id': maintenance.property_id.id,
                    'invoice_line_ids': inv_line_values,
                    'amount_total': maintenance.cost or 0.0,
                    'invoice_date': maintenance.request_date or False,
                }

                move_id = self.env['account.move'].with_context(
                    {'default_type': 'out_invoice'}).create(inv_values)
                maintenance.write({'invoice_check': True, 'invoice_id': move_id.id})
            else:
                inv_line_values.append((0, 0, {
                    'name': 'Maintenance For ' + maintenance.name or "",
                    'ref': 'Maintenance Request',
                    'quantity': 1,
                    'account_id': maintenance.account_id.id or False,
                    'price_unit': maintenance.cost or 0.00,
                }))
                for tenancy_data in tenancy_ids:
                    inv_values = {
                        'invoice_origin': 'Maintenance Invoice' or "",
                        'move_type': 'out_invoice',
                        'property_id': maintenance.property_id.id,
                        'invoice_line_ids': inv_line_values,
                        'amount_total': maintenance.cost or 0.0,
                        'invoice_date': maintenance.request_date or False,
                        # 'number': tenancy_maintenance.name or '',
                    }
                if maintenance.renters_fault:
                    inv_values.update({
                        'partner_id':
                        tenancy_data.tenant_id.parent_id.id or False})
                else:
                    inv_values.update(
                        {'partner_id':
                            tenancy_data.property_id.property_manager.id or
                            False})

                move_id = self.env['account.move'].create(inv_values)
                maintenance.write({
                    'invoice_check': True,
                    'invoice_id': move_id.id,
                })

    def open_invoice(self):
        """
        This Method is used to Open invoice from maintenance record.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        wiz_form_id = self.env.ref('account.view_move_form').id
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class MaintenanceStage(models.Model):
    _inherit = 'maintenance.stage'

    is_in_progress = fields.Boolean(
        string='In Progress',
        default=False)
