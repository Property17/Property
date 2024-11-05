# See LICENSE file for full copyright and licensing details

from datetime import datetime

from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TenancyRentSchedule(models.Model):
    _name = "tenancy.rent.schedule"
    _description = 'Tenancy Rent Schedule'
    _rec_name = "tenancy_id"
    _order = 'start_date'

    @api.depends('invoice_id.state')
    def compute_move_check(self):
        """
        This method check if invoice state is paid true then move check field.
        @param self: The object pointer
        """
        for data in self:
            data.move_check = bool(data.move_id)
            if data.invoice_id and data.invoice_id.state == 'posted':
                data.move_check = True

    @api.depends('invoice_id', 'invoice_id.amount_residual')
    def compute_paid(self):
        """
        If  the invoice state in paid state then paid field will be true.
        @param self: The object pointer
        """
        self.paid = False
        for data in self:
            # if data.invoice_id and data.invoice_id.state == 'paid':
            if data.invoice_id and data.invoice_id.amount_residual == 0:
                data.paid = True

    note = fields.Text(
        string='Notes',
        help='Additional Notes.')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Currency',
        required=True)
    amount = fields.Monetary(
        string='Amount',
        default=0.0,
        currency_field='currency_id',
        help="Rent Amount.")
    start_date = fields.Date(
        string='Date',
        help='Start Date.')
    end_date = fields.Date(
        string='End Date',
        help='End Date.')
    cheque_detail = fields.Char(
        string='Cheque Detail',
        size=30)
    move_check = fields.Boolean(
        compute='compute_move_check',
        string='Posted',
        store=True)
    rel_tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string="Tenant", related='tenancy_id.tenant_id', store=True)
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Depreciation Entry')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        help='Property Name.')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        domain="[('is_property', '=', True)]",
        help='Tenancy Name.', required=True)
    paid = fields.Boolean(
        compute='compute_paid',
        store=True,
        string='Paid',
        help="True if this rent is paid by tenant")
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')
    is_invoiced = fields.Boolean(
        string='Invoiced?')
    rent_residual = fields.Monetary(
        string='Pending Amount',
        related="invoice_id.amount_residual",
        currency_field='currency_id',
        help="Pending Ammount.")
    is_readonly = fields.Boolean(
        string='Readonly')

    def get_invloice_lines(self):
        """TO GET THE INVOICE LINES"""
        inv_line = {}
        for rec in self:
            inv_line = {
                # 'origin': 'tenancy.rent.schedule',
                'name': _('Tenancy(Rent) Cost'),
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'account_id':
                rec.tenancy_id.property_id.income_acc_id.id or False,
                # 'analytic_distribution': rec.tenancy_id.id or False,
                'analytic_distribution': {rec.tenancy_id.id : 100} if rec.tenancy_id else {},
            }
            # if rec.tenancy_id:
            #     inv_line['analytic_distribution'] =  {rec.tenancy_id.id : 100}
            #     inv_line.append((0, 0, inv_line))
        return [(0, 0, inv_line)]

    def create_invoice(self):
        """
        Create invoice for Rent Schedule.
        @param self: The object pointer
        """
        inv_obj = self.env['account.move']
        for rec in self:
            inv_line_values = rec.get_invloice_lines()
            inv_values = {
                'partner_id': rec.tenancy_id.tenant_id.parent_id.id or False,
                'move_type': 'out_invoice',
                'property_id': rec.tenancy_id.property_id.id or False,
                'invoice_date': rec.start_date or False,
                'invoice_line_ids': inv_line_values,
                'new_tenancy_id': rec.tenancy_id.id,
                'auto_post': 'at_date'
            }
            invoice_id = inv_obj.create(inv_values)
            rec.write({'invoice_id': invoice_id.id, 'is_invoiced': True})
            inv_form_id = self.env.ref('account.view_move_form').id

        return {
            'view_type': 'form',
            'view_id': inv_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def open_invoice(self):
        """
        Description:
            This method is used to open invoce which is created.

        Decorators:
            api.multi
        """
        return {
            'view_type': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def send_mail_tenant_rent_schedule(self):
        template_id = self.env.ref('property_management.mail_tenant_rent')
        today = fields.Date.context_today(self)
        rent_ids = self.env['tenancy.rent.schedule'].search(
            [('paid', '=', False)])
        for schedule in rent_ids:
            if schedule.start_date and (schedule.start_date - today).days <= 7:
                from_email = \
                    schedule.tenancy_id.property_id.property_manager.email
                to_email = schedule.tenancy_id.tenant_id.email

                template_id.write({
                    'email_to': to_email,
                    'email_from': from_email,
                })
                d = template_id.send_mail(schedule.id, force_send=True)
        return True
