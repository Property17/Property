# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError


class CommissionInvoiceLine(models.Model):
    _name = "commission.invoice.line"
    _description = "Commission Invoice Line"
    _order = 'date desc, id desc'

    date = fields.Date(
        string='Start Date')
    end_date = fields.Date(
        string='End Date')
    name = fields.Char(
        string="Description")
    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type')
    rent_amt = fields.Float(
        string='Rent Amount')
    amount = fields.Float(
        store=True,
        string='Commission Amount')
    commission_id = fields.Many2one(
        comodel_name='commission.invoice',
        string='Commission')
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')
    invoice_check = fields.Boolean(
        string='INV')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="OwnerCompany")
    currency_id = fields.Many2one(
        related='commission_id.currency_id',
        comodel_name="res.currency",
        string="Currency")
    invoiced = fields.Boolean(
        string='Invoiced')

    @api.constrains('date', 'end_date')
    def _constraint_date_limit(self):
        """
        This method is use to Validate a Date Constrain
        -----------------------------------------------------------------
        """
        for rec in self:
            if rec.date and rec.end_date:
                if rec.end_date < rec.date:
                    raise ValidationError(_('Commission Information end date '
                                            'must be greater or equals to '
                                            'start date !'))
            return True

class CommissionInvoice(models.Model):
    _name = "commission.invoice"
    _rec_name = 'number'
    _description = "Commission Invoice"

    @api.depends('commission_line.amount')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        self.amount_total = 0.0
        for data in self.commission_line:
            self.amount_total += data.amount

    number = fields.Char(
        string='Commission ID',
        default='/')
    patner_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Partner',
        help='Name of tenant where from commission is taken')
    date = fields.Date(
        string='Commission Date',
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT))
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    description = fields.Text(
        string='Description')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    state = fields.Selection(
        [('draft', 'Open'),
         ('cancel', 'Cancel'),
         ('invoice', 'Invoiced')
         ], 'State', readonly=True,
        default='draft')
    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type',
        default='fixed')
    commission_line = fields.One2many(
        comodel_name='commission.invoice.line',
        inverse_name='commission_id',
        string='Commission')
    amount_total = fields.Float(
        string='Total',
        store=True,
        readonly=True,
        compute='_amount_all')
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency")
    agent = fields.Many2one(
        comodel_name='res.partner',
        domain=[('agent', '=', True)])
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id)
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')
    invoice_check = fields.Boolean(
        string='INV')
    color = fields.Integer('Color Index')

    @api.onchange('tenancy')
    def parent_tenancy_onchange(self):
        """
        when you change tenancy, this method will change
        property, agent, partner and currency fields values accordingly.
        @param self: The object pointer
        """
        if self.tenancy:
            self.agent = self.tenancy.agent.id or False
            self.property_id = self.tenancy.property_id.id or False
            self.patner_id = self.tenancy.tenant_id.id or False
            self.currency_id = self.tenancy.currency_id.id or False

    def create_invoice(self):
        """
        This method is used to create supplier invoice.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        for data in self:
            inv_line_values = {
                'name': 'Commission For ' + data.number or "",
                # 'analytic_distribution': data.tenancy.id or False,
                'analytic_distribution': {data.tenancy_id.id : 100} if data.tenancy_id else {},
                # 'origin': 'Commission',
                'quantity': 1,
                'account_id': data.property_id.expense_account_id.id or False,
                'price_unit': data.amount_total or 0.00,
                'currency_id': data.currency_id.id or False
            }
            inv_values = {
                'invoice_origin': 'Commission For ' + data.number or "",
                'move_type': 'in_invoice',
                'property_id': data.property_id.id,
                'partner_id': data.agent.id or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'invoice_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                # 'account_id':
                # data.agent.property_account_payable_id.id or False,
                'journal_id': account_jrnl_obj and account_jrnl_obj.id or False,
                'currency_id': data.currency_id.id or False,
            }
            acc_id = self.env['account.move'].with_context(
                {'default_type': 'in_invoice'}).create(inv_values)
            data.write({'invoice_check': True, 'invoice_id': acc_id.id, 'state': 'invoice'})
        return {
            'view_type': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': self._context,
        }

    def open_invoice(self):
        """
        This Method is used to Open invoice .
        ------------------------------------
        @param self: The object pointer
        """
        context = dict(self._context or {})
        return {
            'view_type': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }

    @api.model
    def create(self, vals):
        """
        This Method is used to create sequence for commission.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        res = super(CommissionInvoice, self).create(vals)
        if res:
            res.number = self.env['ir.sequence'].get('commission.invoice')
        return res

    def button_close(self):
        """
        This button method is used to Change commission state to cancel.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        if not self.tenancy.state == 'close' or \
                self.tenancy.state == 'cancelled':
            raise ValidationError(_("Please First close " + str(
                self.tenancy.name) + " Tenancy!"))
        return self.write({'state': 'cancel'})

# TODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODO
# class AccountPayment(models.Model):
#     _inherit = 'account.payment'

   
#     def post(self):
#         """
#         This method is used to check if the invoice state is paid then
#         the PAID will be true.
#         ------------------------------------------------------------
#         @param self: The object pointer
#         """
        

#         res = super(AccountPayment, self).post()
#         commission_obj = self.env['commission.invoice']
#         for data in commission_obj.commission_line.browse(
#                 self._context.get('active_id')):
#             if data:
#                 line_obj = self.env['commission.invoice.line'].search(
#                     [('invoice_id', '=', data.id)])
                
#                 for data1 in line_obj:
#                     if data1.invoice_id.state == 'posted':
#                         data1.invoiced = True
#         return res


# class TenancyRentSchedule(models.Model):
#     _inherit = "tenancy.rent.schedule"
#     _description = "Commission Invoice"


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.depends('commission_type', 'fix_qty', 'fix_cost', 'total_rent')
    def calculate_commission(self):
        """
        This method is used to calculate commistion as per commition type
        -----------------------------------------------------------------
        @param self: The object pointer
        """
        self.total_commission = 0.0
        for data in self:
            if data.commission == True:
                if data.commission_type == 'fixed':
                    data.total_commission = data.total_rent * (
                        data.fix_qty / 100.0)
                if data.commission_type == 'fixedcost':
                    data.total_commission = data.fix_cost

    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type')
    fix_qty = fields.Float(
        string='Fixed Percentage(%)')
    fix_cost = fields.Float(
        string='Fixed Cost')
    agent = fields.Many2one(
        comodel_name='res.partner',
        domain=[('agent', '=', True)])
    commission = fields.Boolean(
        'Commission')
    commission_create = fields.Boolean(
        'Create')
    total_commission = fields.Float(
        string="Total Commission",
        compute="calculate_commission")

    def create_commission(self):
        """
        This button method is used to Change Tenancy state to Open.
        -----------------------------------------------------------
        @param self: The object pointer
        """
        for data in self:
            if data.total_commission == 0.00:
                raise ValidationError(
                    _('Total Commission must be grater than zero.'))
            line_vlas = {
                'name': 'Commission',
                'commission_type': data.commission_type,
                'rent_amt': data.total_rent,
                'date': data.date_start,
                'end_date': data.date,
                'amount': data.total_commission,
            }
            vals = {
                'patner_id': data.tenant_id.id,
                'tenancy': data.id,
                'property_id': data.property_id.id,
                'agent': data.agent.id,
                'currency_id': data.currency_id.id or False,
                'commission_line': [(0, 0, line_vlas)],
            }
            self.env['commission.invoice'].create(vals)
            data.write({'commission_create': True})

    # @api.onchange('commission')
    # def onchange_property_id(self):
    #     """
    #     This method is used to check if the commistion field False than
    #     othe field value will be null or zero or false.
    #     ---------------------------------------------------------------
    #     @param self: The object pointer
    #     """
    #     if self.commission is False:
    #         self.agent = 0
    #         self.commission_type = False
    #         self.fix_qty = 0.00
    #         self.fix_cost = 0.00
    
    @api.onchange('commission')
    def onchange_commission(self):
        """
        This method checks if the commission field is False, 
        then sets other fields to their default values.
        """
        if self.commission is False:
            self.agent = False  
            self.commission_type = False  
            self.fix_qty = 0.00
            self.fix_cost = 0.00        
