from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class DiscountRent(models.Model):
    _name = "discount.rent"
    _description = "Discount Rent"
    _rec_name = "tenancy_id"
    _order = "id desc"

    
    tenancy_id = fields.Many2one('account.analytic.account', string='Tenancy')
    tenancy_rent_id = fields.Many2one('tenancy.rent.schedule', string='Tenancy Rent')
    date = fields.Date(string='Date', default=fields.Date.today())
    description = fields.Char(string="Description")
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    discount = fields.Float(string="Discount")
    discount_type = fields.Selection(
        [('fixed_amount', 'Fixed Amount'), ('percentage', 'Percentage'), ],
       string='Discount Type', default='fixed_amount' )
    discount_amount = fields.Float(string="Discount Amount", compute="_compute_discount_amount", store=True)
    status = fields.Selection(
        [('active', 'Active'), ('not_active', 'Not Active'), ],default='not_active',
       string='Status', copy=False )
    property_id = fields.Many2one('account.asset', string='Property')
    properties = fields.Text(related='tenancy_id.multi_properitis', string='Property')
    tenant_id = fields.Many2one('tenant.partner', related='tenancy_id.tenant_id', string='Tenant')
    rent = fields.Monetary(string="Rent", related='tenancy_id.rent' )
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    
    def action_set_inactive(self):
        """Button method to deactivate discount and remove applied discount from rent lines"""
        for rec in self:
            rec.status = "not_active"

            if not rec.tenancy_id or not rec.start_date:
                continue  # skip if no tenancy or start_date is set

            # Build same domain used in apply_discount_to_rent
            domain = [
                ('tenancy_id', '=', rec.tenancy_id.id),
                ('start_date', '>=', rec.start_date),
            ]

            if rec.end_date:
                domain.append(('start_date', '<=', rec.end_date))

            domain.append(('invoice_id', '=', False))

            rent_lines = self.env['tenancy.rent.schedule'].search(domain)

            # Reset discount_amount to 0 on these lines
            rent_lines.write({'discount_amount': 0.0})
    
    
    # def action_set_inactive(self):
    #     """Button method to deactivate discount manually"""
    #     for rec in self:
    #         rec.status = "not_active"
        
    @api.depends('discount', 'discount_type', 'rent')
    def _compute_discount_amount(self):
        for rec in self:
            if rec.discount_type == 'fixed_amount':
                rec.discount_amount = rec.discount
            elif rec.discount_type == 'percentage' and rec.rent:
                rec.discount_amount = (rec.discount / 100.0) * rec.rent
            else:
                rec.discount_amount = 0.0
    
    def apply_discount_to_rent(self):
        for rec in self:
            if not rec.tenancy_id or not rec.start_date:
                raise ValidationError("Please set the Tenancy and Start Date.")

            domain = [
                ('tenancy_id', '=', rec.tenancy_id.id),
                ('start_date', '>=', rec.start_date),
            ]

            if rec.end_date:
                domain.append(('start_date', '<=', rec.end_date))

            # domain.append(('move_check', '=', False))
            domain.append(('invoice_id', '=', False))

            rent_lines = self.env['tenancy.rent.schedule'].search(domain)
            
            if not rent_lines:
                raise ValidationError("No rent schedule lines found matching the criteria.")

            for line in rent_lines:                
                line.discount_amount = rec.discount_amount
                rec.status = 'active'

        return True
    
    

class ServicesType(models.Model):
    
    _name = "services.type"
    _description = "Services Type"
    _rec_name = "name"
    _order = "id desc"
    
    name = fields.Char('Type')
    amount = fields.Float('Amount')
    service_account_id = fields.Many2one('account.account', string="Service Account")

    
class ServicesRent(models.Model):
    _name = "service.rent"
    _description = "Services Rent"
    _order = "id desc"
    
    service_type_id = fields.Many2one('services.type', string='Type')
    tenancy_id = fields.Many2one('account.analytic.account', string='Tenancy')
    tenancy_rent_id = fields.Many2one('tenancy.rent.schedule', string='Tenancy Rent')
    date = fields.Date(string='Date', default=fields.Date.today())
    amount = fields.Float('Amount', related='service_type_id.amount', readonly=False)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    move_id = fields.Many2one('account.move', string='Invoice')
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    paid = fields.Boolean(
        compute='compute_paid',
        store=True,
        string='Paid',
        help="True if this rent is paid by tenant")
    posted = fields.Boolean(
        compute='compute_move_check',
        string='Posted',
        store=True)
    is_created = fields.Boolean()
    is_invoiced = fields.Boolean(
        string='Invoiced?')
    service_account_id = fields.Many2one('account.account', related='service_type_id.service_account_id', string="Service Account")


    
    @api.depends('move_id.state')
    def compute_move_check(self):
        """
        This method check if invoice state is paid true then move check field.
        @param self: The object pointer
        """
        for data in self:
            data.posted = bool(data.move_id)
            if data.move_id.state == 'posted':
                data.posted = True
            else:
                data.posted = False
    
    @api.depends('move_id', 'move_id.amount_residual')
    def compute_paid(self):
        """
        If  the invoice state in paid state then paid field will be true.
        @param self: The object pointer
        """
        self.paid = False
        for data in self:
            if data.move_id and data.move_id.amount_residual == 0:
                data.paid = True
                
                
    def print_invoice_report(self):
        return self.env.ref('pyment_report.mm_multi_invoice_report_action').report_action(self.move_id.id)

    def get_invloice_lines(self):
        """TO GET THE INVOICE LINES"""
        inv_line = {}
        for rec in self:
            inv_line = {
                'name': rec.service_type_id.name,
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'account_id': rec.service_account_id.id or False,
                'analytic_account_id': rec.tenancy_id.id,
                'analytic_distribution': {rec.tenancy_id.id : 100} if rec.tenancy_id else {},
            }
            if self.tenancy_id.multi_prop:
                for data in self.tenancy_id.prop_ids:
                    if data.property_id and data.property_id.income_acc_id:
                        for account in data.property_id.income_acc_id:
                            account_id = account.id
                        inv_line.update({'account_id': account_id})
                        
        return [(0, 0, inv_line)]

    def create_invoice(self):
        """
        Create invoice for Rent Schedule.
        @param self: The object pointer
        """
        inv_obj = self.env['account.move']
        for rec in self:
            prop_lines = []
            for rent_line in rec.tenancy_id.prop_ids:
                prop_lines.append((0, 0, {
                    'property_id': rent_line.property_id.id,
                    'ground': rent_line.ground or 0.0,
                }))
            
            inv_line_values = rec.get_invloice_lines()
            inv_values = {
                'partner_id': rec.tenancy_id.tenant_id.parent_id.id or False,
                'move_type': 'out_invoice',
                'property_id': rec.tenancy_id.property_id.id or False,
                'tenancy_id': rec.tenancy_id.id or False,
                'invoice_date': rec.date or False,
                'multi_properitis': rec.tenancy_id.multi_properitis or False,
                'invoice_line_ids': inv_line_values,
                'new_tenancy_id': rec.tenancy_id.id,
                'auto_post': 'at_date',
                'prop_ids': prop_lines,
                'plan_id': rec.tenancy_id.plan_id.id,
                'company_id': rec.tenancy_id.company_id.id,

            }
            invoice_id = inv_obj.with_company(rec.tenancy_id.company_id.id).create(inv_values)

            for line in invoice_id.line_ids:
                if line.account_id.account_type == 'asset_receivable':
                    line.analytic_account_id = rec.tenancy_id.id
                else:
                    line.analytic_account_id= False
            
                     
            rec.write({'move_id': invoice_id.id, 'is_invoiced': True})
        inv_form_id = self.env.ref('account.view_move_form').id
        self.is_created = True
        

        return {
            'view_type': 'form',
            'view_id': inv_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
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
            'res_id': self.move_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }




class ServicesSchedule(models.Model):
    _name = "service.schedule"
    _description = "Services Schedule"
    _order = "id desc"
    
    service_type_id = fields.Many2one('services.type', string='Type')
    tenancy_id = fields.Many2one('account.analytic.account', string='Tenancy')
    tenancy_rent_id = fields.Many2one('tenancy.rent.schedule', string='Tenancy Rent')
    date = fields.Date(string='Date', default=fields.Date.today())
    amount = fields.Float('Amount', readonly=False, store=True)
    move_id = fields.Many2one('account.move', string='Invoice')
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    
    @api.onchange('service_type_id')
    def onchange_service_type(self):
        for rec in self:
            if rec.service_type_id:
                rec.amount = rec.service_type_id.amount
    
   


    