from num2words import num2words
from .money_to_text_ar import amount_to_text_arabic
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime
from datetime import date, datetime, time
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class AccountMoveInheritNew(models.Model):
    _inherit = "account.move"
    _order = "invoice_date ASC"
    


    user_paid_by_id = fields.Many2one('res.users', string="Paid By")
    paid_date = fields.Date()
    mm_journal_id = fields.Many2one('account.journal')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.', required=0)
    property_manager_id = fields.Many2one('res.partner', string='Property Manager', related='tenancy_id.property_manager_id', store=True)
    property_id = fields.Many2one('account.asset', string='Property', related='tenancy_id.property_id', store=True)
    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', related='tenancy_id.analytic_account_id', store=True)
    cheque_detail = fields.Char(string='Cheque Detail',)
    rent_residual = fields.Monetary(string='Pending Amount', currency_field='currency_id',)
    note = fields.Text(string='Notes')
    plan_id = fields.Many2one(
        comodel_name='account.analytic.plan',
        string='Analytic Plan')
    
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
            ('blocked', 'Blocked'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    state_ch = fields.Char()
    run_comp = fields.Boolean('Run Comp')
    multi_properitis = fields.Text(
        string='Properties',
        help="Multiple property.",
        store=True)
    
    properitis = fields.Text(
        string='Properties',
        help="Multiple property.", compute="_compute_properitis",
        store=True)
    # run_comp = fields.Boolean(compute='_compute_analytic_account')
    
    hide_reset_to_draft = fields.Boolean(compute='_compute_hide_reset_to_draft', store=True)

    @api.depends('amount_total', 'amount_residual')
    def _compute_hide_reset_to_draft(self):
        for move in self:
            amount_paid = move.amount_total - move.amount_residual
            move.hide_reset_to_draft = move.amount_total > 0 and amount_paid > 0

    def _compute_payment_reference(self):
        for move in self.filtered(lambda m: (
            m.state == 'posted'
            and m.move_type == 'out_invoice'
            and not m.payment_reference
        )):
            move.payment_reference = ''
        self._inverse_payment_reference()


    @api.depends('multi_properitis', 'property_id')
    def _compute_properitis(self):
        for record in self:
            if record.property_id:
                record.properitis = record.property_id.name
            else:
                record.properitis = record.multi_properitis
    
   

    def action_update_fields(self):
        for rec in self:
            if rec.tenancy_id:
                tenancy_rent = self.env['tenancy.rent.schedule'].search([('tenancy_id', '=', self.tenancy_id.id), ('invoice_id', '=', self.id)])
                if rec.cheque_detail:
                    tenancy_rent.cheque_detail = rec.cheque_detail
                if rec.note:
                    tenancy_rent.note = rec.note
    
                      

    # def _compute_analytic_account(self):
    #     for rec in self:
    #         rec.run_comp = True
    #         if rec.tenancy_id:
    #             for line in rec.invoice_line_ids:
    #                 if line.account_id.user_type_id.id == self.env.ref("account.data_account_type_receivable").id:
    #                     if not line.analytic_distribution:
    #                         line.analytic_distribution = rec.tenancy_id.id
    #                 else:
    #                     line.analytic_distribution = False


class AccountPaymentRegisterInheritNew(models.TransientModel):
    _inherit = "account.payment.register"
    

    
    @api.depends('can_edit_wizard')
    def _compute_communication(self):
        # The communication can't be computed in '_compute_from_lines' because
        # it's a compute editable field and then, should be computed in a separated method.
        for wizard in self:
            pass
            # if wizard.can_edit_wizard:
            #     batches = wizard._get_batches()
            #     wizard.communication = wizard._get_batch_communication(batches[0])
            # else:
            #     wizard.communication = False
    

    
    @api.model
    def default_get(self, fields_list):
        res = super(AccountPaymentRegisterInheritNew, self).default_get(fields_list)
        context = self.env.context
        invoice_obj = self.env['account.move']
        if self._context.get('active_id'):
            invoice_id = invoice_obj.browse(context['active_id'])
            res['tenancy_id'] = invoice_id.tenancy_id.id
        return res
    
 
    # def action_create_payments(self):
    #     active_id = self._context.get('active_ids') or self._context.get('active_id')
    #     account_move = self.env['account.move'].search([('id', '=', active_id)])
    #     tenancy_rent = self.env['tenancy.rent.schedule'].search(
    #         [('tenancy_id', '=', account_move.tenancy_id.id), ('start_date', '<=', account_move.invoice_date)])
    #     if tenancy_rent:
    #         for line in tenancy_rent:
    #             if not line.paid:
    #                 if line.invoice_id.id != account_move.id:
    #                     raise UserError(
    #                         _('You cannot paid this entry please paid this entry first: %s ') % (line.invoice_id.name,))
    #                 else:
    #                     account_move.user_paid_by_id = self.env.user.id
    #                     account_move.mm_journal_id = self.journal_id.id
    #                     account_move.paid_date = self.payment_date

    #                     payments = self._create_payments()

    #                     if self._context.get('dont_redirect_to_payments'):
    #                         return True
    #                     action = {
    #                         'name': _('Payments'),
    #                         'type': 'ir.actions.act_window',
    #                         'res_model': 'account.payment',
    #                         'context': {'create': False},
    #                     }
    #                     if len(payments) == 1:
    #                         action.update({
    #                             'view_mode': 'form',
    #                             'res_id': payments.id,
    #                         })
    #                         # pay = self.env['account.payment'].search([('id', '=', payments.id)])
    #                         # if pay.move_id:
    #                         #     pay.move_id._compute_analytic_account()

    #                     else:
    #                         action.update({
    #                             'view_mode': 'tree,form',
    #                             'domain': [('id', 'in', payments.ids)],
    #                         })
    #                         # pay2 = self.env['account.payment'].search([('id', 'in', payments.ids)])
    #                         # for p in pay2:
    #                         #     if p.move_id:
    #                         #         p.move_id._compute_analytic_account()
    #                     return action
    #     else:
    #         account_move.user_paid_by_id = self.env.user.id
    #         account_move.mm_journal_id = self.journal_id.id
    #         account_move.paid_date = self.payment_date

    #         payments = self._create_payments()

    #         if self._context.get('dont_redirect_to_payments'):
    #             return True

    #         action = {
    #             'name': _('Payments'),
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'account.payment',
    #             'context': {'create': False},
    #         }
    #         if len(payments) == 1:
    #             action.update({
    #                 'view_mode': 'form',
    #                 'res_id': payments.id,
    #             })
    #             # pay = self.env['account.payment'].search([('id', '=', payments.id)])
    #             # if pay.move_id:
    #             #     pay.move_id._compute_analytic_account()

    #         else:
    #             action.update({
    #                 'view_mode': 'tree,form',
    #                 'domain': [('id', 'in', payments.ids)],
    #             })
    #             # pay2 = self.env['account.payment'].search([('id', 'in', payments.ids)])
    #             # for p in pay2:
    #             #     if p.move_id:
    #             #         p.move_id._compute_analytic_account()
    #         return action

    # def _create_payment_vals_from_wizard(self):
    #     active_id = self._context.get('active_ids') or self._context.get('active_id')
    #     account_move = self.env['account.move'].search([('id', '=', active_id)])
    #     res = super()._create_payment_vals_from_wizard()
    #     res.update({'tenancy_id': account_move.tenancy_id.id if account_move.tenancy_id.id else False,})
    #     return res
    
    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super(AccountPaymentRegisterInheritNew, self)._create_payment_vals_from_wizard(batch_result)
        payment_vals['tenancy_id'] = self.tenancy_id.id
        payment_vals['tenancy_id'] = self.tenancy_id.id

        return payment_vals
    


class AccountAssetAssetNew(models.Model):
    _inherit = "account.asset"

    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    auto_add_no = fields.Char(string='Auto - Address No ')
    # plan_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    plan_id = fields.Many2one(
        comodel_name='account.analytic.plan',
        string='Analytic Plan')
    
    serial_number = fields.Integer('Serial Number')
    service_account_id = fields.Many2one('account.account', string="Service Account")


    # @api.onchange('parent_id')
    # def _onchange_parent_id(self):
    #     for rec in self:
    #         if rec.parent_id:
    #             rec.analytic_account_id = rec.parent_id.analytic_account_id.id


class AccountPaymentInhNew(models.Model):
    _inherit = "account.payment"

    date_ch = fields.Char(compute='_compute_get_date')
    mm_invoice_id = fields.Many2one('account.move', string="Invoice")
    is_deposit_receive = fields.Boolean('Is Deposit Receive')
    
    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)
    
    
    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        """Override to add analytic account to journal items during payment"""
        move_line_vals = super(AccountPaymentInhNew, self)._prepare_move_line_default_vals(write_off_line_vals)
        
        # Apply the analytic account to all move lines generated by this payment
        for move_line in move_line_vals:
            # Ensure the 'credit' key exists before checking its value
            if move_line.get('credit', 0) > 0:
                if self.is_deposit_receive:
                    move_line.update({
                        'account_id': self.partner_id.tenancy_insurance_id.id
                    })
                if self.tenancy_id and not self.is_deposit_receive:
                    move_line['analytic_account_id'] = self.tenancy_id.id

        return move_line_vals

    
    # def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
    #     """Override to add analytic account to journal items during payment"""
    #     move_line_vals = super(AccountPaymentInhNew, self)._prepare_move_line_default_vals(write_off_line_vals)
    #     # Apply the analytic account to all move lines generated by this payment
    #     for move_line in move_line_vals:
    #         if self.is_deposit_receive == True:
    #             if move_line.get('credit') > 0:
    #                 move_line.update({
    #                         'account_id': self.partner_id.tenancy_insurance_id.id
    #                 })
    #         if move_line['credit'] > 0:
    #             if self.tenancy_id and self.is_deposit_receive != True:
    #             # if self.tenancy_id:
    #                 move_line['analytic_account_id'] = self.tenancy_id.id

    #     return move_line_vals


    def _compute_get_date(self):
        for rec in self:
            for line in rec.reconciled_invoice_ids:
                rec.mm_invoice_id = line.id
            if rec.date:
                invoice_date = fields.Date.from_string(rec.invoice_date) or fields.Date.from_string(rec.date)
                ttyme = datetime.combine(invoice_date, time.min)
                locale = self.env.context.get('lang', 'en_US')
                sheet_name = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))
                rec.date_ch = sheet_name


class TenantPartnerNew(models.Model):
    _inherit = "tenant.partner"

    civil_number = fields.Char(string='Civil Number')
    country_id = fields.Many2one('res.country', 'Nationality')

    name2 = fields.Char(string='Represented In Name')
    civil_number2 = fields.Char(string='Represented Civil Number')
    country_id2 = fields.Many2one('res.country', 'Represented Nationality')
    notes2 = fields.Text('Represented Notes')

    name3 = fields.Char(string="Partner's Name ")
    civil_number3 = fields.Char(string='Partner Civil Number')
    country_id3 = fields.Many2one('res.country', 'Partner Nationality')
    notes3 = fields.Text('Partner Notes')

    work_address = fields.Char(string='Work Address')
    


class TenancyRentScheduleNew(models.Model):
    _inherit = "tenancy.rent.schedule"

    is_blocked = fields.Boolean()
    is_created = fields.Boolean()
    # discount_fixed = fields.Float(string="Discount Fixed")
    discount_amount = fields.Float(string="Discount Amount")
    service_amount = fields.Float(string="Service Amount", store=True, compute="compute_service_amount")
    
    @api.depends('tenancy_id.service_schedule_ids.amount')
    def compute_service_amount(self):
        for rec in self:
            if not rec.move_check:
                rec.service_amount = sum(
                    line.amount for line in rec.tenancy_id.service_schedule_ids if line.amount
                )
                
    @api.onchange('cheque_detail', 'note')
    def _onchange_cheque_detail_notes(self):
        for rec in self:
            if rec.invoice_id:
                if rec.cheque_detail:
                    rec.invoice_id.cheque_detail = rec.cheque_detail
                if rec.note:
                    rec.invoice_id.note = rec.note

    def print_invoice_report(self):
        return self.env.ref('pyment_report.mm_multi_invoice_report_action').report_action(self.invoice_id.id)
    
    def get_invoice_lines(self):
        """Generate invoice lines for rent and related services."""
        invoice_lines = []
        
        for rec in self:
            # Rent invoice line
            rent_line = {
                'name': _('Tenancy(Rent) Cost'),
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'account_id': rec.tenancy_id.property_id.income_acc_id.id or False,
                'analytic_account_id': rec.tenancy_id.id,
                'analytic_distribution': {str(rec.tenancy_id.id): 100} if rec.tenancy_id else {},
                # 'discount_fixed': rec.discount_amount or 0.00,
            }
            
            # Update account_id for multi-property tenancies
            if rec.tenancy_id.multi_prop:
                for data in rec.tenancy_id.prop_ids:
                    if data.property_id and data.property_id.income_acc_id:
                        rent_line.update({'account_id': data.property_id.income_acc_id.id})
            
            invoice_lines.append((0, 0, rent_line))
            
            if rec.discount_amount > 0.00:
                discount_line = {
                'name': _('Tenancy(Discount) Cost'),
                'price_unit': -rec.discount_amount or 0.00,
                'quantity': 1,
                'account_id': rec.tenancy_id.property_id.discount_account_id.id or False,
                # 'analytic_account_id': rec.tenancy_id.id,
                # 'analytic_distribution': {str(rec.tenancy_id.id): 100} if rec.tenancy_id else {},
                }
                if rec.tenancy_id.multi_prop:
                    for data in rec.tenancy_id.prop_ids:
                        if data.property_id and data.property_id.discount_account_id:
                            rent_line.update({'account_id': data.property_id.discount_account_id.id})
                invoice_lines.append((0, 0, discount_line))

            for service in rec.tenancy_id.service_schedule_ids:            
                service_line = {
                    'name': _('Service: %s') % (service.service_type_id.name or 'Unknown Service'),
                    'price_unit': service.amount or 0.00,
                    'quantity': 1,
                    'account_id': (
                        rec.tenancy_id.property_id.service_account_id.id
                        if rec.tenancy_id.property_id and rec.tenancy_id.property_id.service_account_id
                        else service.service_type_id.service_account_id.id
                    ),
                    'analytic_account_id': rec.tenancy_id.id,
                    'analytic_distribution': {str(rec.tenancy_id.id): 100} if rec.tenancy_id else {},
                }
                # Update account_id for multi-property tenancies
                if rec.tenancy_id.multi_prop:
                    for data in rec.tenancy_id.prop_ids:
                        if data.property_id and data.property_id.service_account_id:
                            service_line.update({'account_id': data.property_id.service_account_id.id})
                
                invoice_lines.append((0, 0, service_line))
        
        return invoice_lines

    # def get_invloice_lines(self):
    #     """TO GET THE INVOICE LINES"""
    #     inv_line = {}
    #     for rec in self:
    #         inv_line = {
    #             # 'origin': 'tenancy.rent.schedule',
    #             'name': _('Tenancy(Rent) Cost'),
    #             'price_unit': rec.amount or 0.00,
    #             'quantity': 1,
    #             'account_id': rec.tenancy_id.property_id.income_acc_id.id or False,
    #             # 'analytic_distribution': rec.tenancy_id.id or False,
    #             'analytic_account_id': rec.tenancy_id.id,
    #             'analytic_distribution': {rec.tenancy_id.id : 100} if rec.tenancy_id else {},
    #             'discount_fixed': rec.discount_amount,
    #             # 'discount_fixed': rec.discount_fixed,

    #         }
    #         if self.tenancy_id.multi_prop:
    #             for data in self.tenancy_id.prop_ids:
    #                 if data.property_id and data.property_id.income_acc_id:
    #                     for account in data.property_id.income_acc_id:
    #                         account_id = account.id
    #                     inv_line.update({'account_id': account_id})
                        
    #     return [(0, 0, inv_line)]

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
            
            inv_line_values = rec.get_invoice_lines()
            inv_values = {
                'partner_id': rec.tenancy_id.tenant_id.parent_id.id or False,
                'move_type': 'out_invoice',
                'property_id': rec.tenancy_id.property_id.id or False,
                'tenancy_id': rec.tenancy_id.id or False,
                'invoice_date': rec.start_date or False,
                'cheque_detail': rec.cheque_detail or False,
                'rent_residual': rec.rent_residual or False,
                'note': rec.note or False,
                'multi_properitis': rec.tenancy_id.multi_properitis or False,
                'invoice_line_ids': inv_line_values,
                'new_tenancy_id': rec.tenancy_id.id,
                'auto_post': 'at_date',
                'prop_ids': prop_lines,
                'plan_id': rec.tenancy_id.plan_id.id,
                'company_id': rec.tenancy_id.company_id.id,

            }
            invoice_id = inv_obj.with_company(rec.company_id.id).create(inv_values)
            # for line in invoice_id.invoice_line_ids:
            #     if line.discount_fixed:
            #         # Explicitly compute the percentage discount
            #         line.discount = line._get_discount_from_fixed_discount()
                
            for line in invoice_id.line_ids:
                if line.account_id.account_type == 'asset_receivable':
                    line.analytic_account_id = rec.tenancy_id.id
                else:
                    line.analytic_account_id= False
                
                if line.account_id.account_type == 'income':
                    line.analytic_distribution = {rec.tenancy_id.id : 100} if rec.tenancy_id else {}
                else:
                    line.analytic_distribution = []
                     
            rec.write({'invoice_id': invoice_id.id, 'is_invoiced': True})
        inv_form_id = self.env.ref('account.view_move_form').id
        self.is_created = True
        

        return {
            'view_type': 'form',
            'view_id': inv_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class TenancyCloseWizard(models.TransientModel):
    _name = 'tenancy.close.wizard'
    _description = 'Tenancy Close Wizard'

    tenancy_id = fields.Many2one(
        'account.analytic.account',
        string='Tenancy',
        required=True,
        readonly=True,
    )
    close_date = fields.Date(
        string='Close Date',
        required=True,
    )
    
    def action_confirm_close(self):
        """Confirm closing tenancy but only block if an un-invoiced schedule exists
        in the same month and year as the close date.
        """
        self.ensure_one()
        tenancy = self.tenancy_id

        if not self.close_date:
            raise UserError(_("Please select a close date."))

        # Get the close month and year
        close_month = self.close_date.month
        close_year = self.close_date.year

        # Find rent schedules in the same month/year
        same_month_schedules = tenancy.rent_schedule_ids.filtered(
            lambda r: r.start_date
            and r.start_date.month == close_month
            and r.start_date.year == close_year
        )

        # If there is any schedule in this month that is not invoiced
        unposted_schedules = same_month_schedules.filtered(lambda r: not r.move_check)
        if unposted_schedules:
            raise UserError(_(
                "You cannot close this tenancy.\n"
                "Please create an invoice for the rent schedule(s) in %s %s before closing."
            ) % (self.close_date.strftime('%B'), self.close_date.year))
        
         # Find rent schedules after the close date
        future_schedules = tenancy.rent_schedule_ids.filtered(
            lambda r: r.start_date and r.start_date > self.close_date
        )

        # Check if any of them are already posted (move_check=True)
        posted_schedules = future_schedules.filtered(lambda r: r.move_check)
        if posted_schedules:
            raise UserError("You cannot close this tenancy because some future rent schedules are already invoiced/posted.")

        # Optionally delete any unposted schedules before close date (your rule)
        to_unlink = tenancy.rent_schedule_ids.filtered(
            lambda r: not r.move_check and r.start_date and r.start_date < self.close_date
        )
        to_unlink.unlink()

        # Close tenancy
        tenancy.close_with_date(self.close_date)

        return {'type': 'ir.actions.act_window_close'}
    
 
    
 

class AccountAnalyticAccountNew(models.Model):
    _inherit = "account.analytic.account"
    

    legal_type_id = fields.Many2one('legal.type', string='Legal Type', )
    # activity_type_lo_id = fields.Many2one('activity.type', string='Activity Type', )
    activity_type_name = fields.Text(string='Activity Type')
    property_manager_id = fields.Many2one(comodel_name='res.partner', string='Property Manager')
    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    close_date = fields.Date(string='Close Date')
    legal = fields.Boolean(string='Legal', )
    legal_case = fields.Boolean(string='Legal Case', )
    legal_date = fields.Date(string='Legal Date')
    legal_attachment = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="Legal Attachment")
    property_ids = fields.Many2many('account.asset', 'property_ids0', 'property_ids00', 'property_ids000',
                                    string='Units')

    contract_count = fields.Integer(compute='get_mm_contract_count')
    name = fields.Char('Description', required=False)
    run_comp = fields.Boolean(compute='_compute_run_func')
    plan_id = fields.Many2one(
        comodel_name='account.analytic.plan',
        string='Analytic Plan')
    
    discount_ids = fields.One2many('discount.rent', 'tenancy_id', string='Discount')
    service_ids = fields.One2many('service.rent', 'tenancy_id', string='Services')
    service_schedule_ids = fields.One2many('service.schedule', 'tenancy_id', string='Services Schedule')
    
    show_renew_button = fields.Boolean(
        string='Show Renew Button',
        compute='_compute_show_renew_button',
        store=False,
        readonly=True
    )
    
    def _compute_show_renew_button(self):
        for record in self:
            today = date.today()
            one_month_later = today + relativedelta(months=1)
            
            # Expiring Soon (Next Month)
            expiring_soon = record.date and today <= record.date <= one_month_later
            
            # Already Expired (Open)
            expired_open = record.date and record.date < today and record.state == 'open'
            
            record.show_renew_button = expiring_soon or expired_open
    
    # def button_close(self):
    #     """
    #     Change Tenancy state to close and delete rent_schedule_ids 
    #     that are not move_check = True.
    #     """
    #     for rec in self:
    #         # Find rent schedules that are not confirmed
    #         rent_schedules = rec.rent_schedule_ids.filtered(lambda r: not r.move_check)
    #         # Unlink them (delete from DB)
    #         rent_schedules.unlink()

    #         # Then close tenancy
    #         rec.write({'state': 'close'})
    #         rec.close_date = fields.Date.today()

    
    def button_close(self):
        """Open the tenancy close wizard."""
        self.ensure_one()
        return {
            'name': 'Close Tenancy',
            'type': 'ir.actions.act_window',
            'res_model': 'tenancy.close.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tenancy_id': self.id},
        }

    def close_with_date(self, close_date):
        """
        Close the tenancy — remove rent schedules after close date and update tenancy state/date.
        """
        for rec in self:
            # Find and delete future rent schedules
            future_schedules = rec.rent_schedule_ids.filtered(lambda r: r.start_date and r.start_date > close_date)
            future_schedules.unlink()

            # Update tenancy info
            rec.write({
                'state': 'close',
                'close_date': close_date,
            })
    
    
    def link_invoices_to_rent_schedules(self):
        """Link each rent schedule to the matching invoice based on date and tenancy."""
        for tenancy in self:
            # Get all invoices for this tenancy once
            invoices = self.env['account.move'].search([
                ('new_tenancy_id', '=', tenancy.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel'),
            ])
            
            for rent_schedule in tenancy.rent_schedule_ids:
                # Only process if no invoice is linked yet
                if not rent_schedule.invoice_id and rent_schedule.start_date:
                    # Find invoice matching by date
                    invoice = invoices.filtered(lambda inv: inv.invoice_date == rent_schedule.start_date)
                    
                    if invoice:
                        rent_schedule.invoice_id = invoice[0].id
                        rent_schedule.is_invoiced = True

                        tenancy.message_post(
                            body=(
                                f"Invoice <b>{invoice[0].name or invoice[0].ref}</b> "
                                f"has been linked to rent schedule dated <b>{rent_schedule.start_date}</b>."
                            ),
                            message_type="comment",
                            subtype_xmlid="mail.mt_note",
                        )


    
    @api.depends('partner_id')
    def _compute_display_name(self):
        for analytic in self:
            name = analytic.name
            # pass
            # if analytic.code:
            #     name = f'[{analytic.code}] {name}'
            # if analytic.partner_id.commercial_partner_id.name:
            #     name = f'{name} - {analytic.partner_id.commercial_partner_id.name}'
            analytic.display_name = name
    

    def _compute_run_func(self):
        for rec in self:
            rec.run_comp = True
            rec._compute_total_rent()
            
    @api.depends('rent_schedule_ids', 'rent', 'rent_type_id')
    def _compute_total_rent(self):
        """
        Calculate the Total Rent based on the type of tenancy (Monthly, Yearly, Weekly).
        """
        for tenancy_brw in self:
            tenancy_brw.total_rent = 0
            if tenancy_brw.rent_type_id and tenancy_brw.rent_type_id.name.isdigit():
                rent_duration = int(tenancy_brw.rent_type_id.name)
                if tenancy_brw.rent_type_id.renttype == 'Monthly':
                    tenancy_brw.total_rent = tenancy_brw.rent * rent_duration
                elif tenancy_brw.rent_type_id.renttype == 'Yearly':
                    tenancy_brw.total_rent = tenancy_brw.rent * (rent_duration * 12)
                elif tenancy_brw.rent_type_id.renttype == 'Weekly':
                    tenancy_brw.total_rent = tenancy_brw.rent * (rent_duration / 4)
        

    # @api.depends('rent_schedule_ids', 'rent', 'rent_type_id')
    # def _compute_total_rent(self):
    #     """
    #     This method is used to calculate Total Rent of current Tenancy.
    #     @param self: The object pointer
    #     @return: Calculated Total Rent.
    #     """
    #     for tenancy_brw in self:
    #         tenancy_brw.total_rent = 0
    #         if tenancy_brw.rent_type_id.renttype == 'Monthly':
    #             tenancy_brw.total_rent = tenancy_brw.rent * int(tenancy_brw.rent_type_id.name)
    #         if tenancy_brw.rent_type_id.renttype == 'Yearly':
    #             tenancy_brw.total_rent = tenancy_brw.rent * (int(tenancy_brw.rent_type_id.name) * 12)
    #         if tenancy_brw.rent_type_id.renttype == 'Weekly':
    #             tenancy_brw.total_rent = tenancy_brw.rent * (int(tenancy_brw.rent_type_id.name) / 4)

    def name_get(self):
        res = []
        for analytic in self:
            name = analytic.name
            if analytic.code:
                name = analytic.code
            res.append((analytic.id, name))
        return res
    
 

    # def button_close(self):
    #     """
    #     This button method is used to Change Tenancy state to close.
    #     @param self: The object pointer
    #     """
    #     for rec in self:
    #         rec.write({'state': 'close'})
    #         rec.close_date = fields.Date.today()

    @api.onchange('code')
    def _onchange_mm_code(self):
        for rec in self:
            if rec.code:
                rec.name = str(rec.code)

    @api.model
    def create(self, vals):
        res = super(AccountAnalyticAccountNew, self).create(vals)
        res._onchange_mm_code()
        return res

    def open_mm_contract(self):
        return {
            'name': _('Contract'),
            'domain': [('tenancy_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'property.contract.template',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                'default_tenancy_id': self.id,
            }
        }

    def get_mm_contract_count(self):
        count = self.env['property.contract.template'].search_count([('tenancy_id', '=', self.id)])
        self.contract_count = count

    def button_blocked(self):
        for rec in self:
            for line in rec.rent_schedule_ids:
                if line.invoice_id:
                    line.invoice_id.state_ch = line.invoice_id.state
                    line.invoice_id.state = 'blocked'
                line.is_blocked = True
            rec.write({'state': 'blocked'})

    def button_un_blocked(self):
        for rec in self:
            for line in rec.rent_schedule_ids:
                if line.invoice_id:
                    line.invoice_id.state = line.invoice_id.state_ch
                line.is_blocked = False
            rec.write({'state': 'open'})

    @api.onchange('property_id')
    def _onchange_property_id001(self):
        for rec in self:
            if rec.property_id:
                rec.plan_id = rec.property_id.plan_id.id

    @api.onchange('property_manager_id')
    def domain_property_id(self):
        self.property_id = False
        self.plan_id = False
        return {'domain': {'property_id': [('property_manager', '=', self.property_manager_id.id), ('state', '=','draft'), ('property_sale_rent', '=', 'rent')]}}

    def compute_amount_in_word_en(self, amount):
        if self.env.user.lang == 'en_US':
            num_word = str(self.currency_id.amount_to_text(amount)) + ' only'
            return num_word
        elif self.env.user.lang == 'ar_001':
            num_word = num2words(amount, to='currency', lang=self.env.user.lang)
            num_word = str(num_word) + ' فقط'
            return num_word

    def amount_text_arabic(self, amount):
        return amount_to_text_arabic(amount, self.company_id.currency_id.name)

    def _cron_run_action(self):
        analytic = self.env['account.analytic.account'].sudo().search([('state', '=', 'open')])
        for rec in analytic:
            for line in rec.rent_schedule_ids:
                if not line.is_created:
                    if line.start_date == fields.Date.today():
                        line.create_invoice()
                        line.is_created = True

    # def _cron_run_action(self):
    #     company = self.env['res.company'].search([])
    #     for com in company:
    #         analytic = self.env['account.analytic.account'].sudo().search([('state', '=', 'open'),('company_id', '=', com.id)])
    #         for rec in analytic:
    #             for line in rec.rent_schedule_ids:
    #                 if not line.is_created:
    #                     if line.start_date == fields.Date.today():
    #                         inv_obj = self.env['account.move']
    #                         lines = [(5, 0, 0)]
    #                         vals = {
    #                             # 'origin': 'tenancy.rent.schedule',
    #                             'name': _('Tenancy(Rent) Cost'),
    #                             'price_unit': line.amount or 0.00,
    #                             'quantity': 1,
    #                             'account_id': line.tenancy_id.property_id.income_acc_id.id or False,
    #                             'analytic_account_id': line.tenancy_id.id or False,
    #                         }
    #                         lines.append((0, 0, vals))
    #                         inv_line_values = lines
    #                         inv_values = {
    #                             'partner_id': line.tenancy_id.tenant_id.parent_id.id or False,
    #                             'move_type': 'out_invoice',
    #                             'property_id': line.tenancy_id.property_id.id or False,
    #                             'tenancy_id': line.tenancy_id.id or False,
    #                             'invoice_date': line.start_date or False,
    #                             'cheque_detail': line.cheque_detail or False,
    #                             'rent_residual': line.rent_residual or False,
    #                             'note': line.note or False,
    #                             'invoice_line_ids': inv_line_values,
    #                             'new_tenancy_id': line.tenancy_id.id,
    #                             'company_id': line.company_id.id,
    #                             'auto_post': True
    #                         }
    #                         print("inv_values", inv_values)
    #                         invoice_id = inv_obj.create(inv_values)
    #                         line.write({'invoice_id': invoice_id.id, 'is_invoiced': True, 'is_created': True})
    #                         line.is_created = True

    def _cron_old_invoice_run_action(self):
        active_id = self._context.get('active_ids') or self._context.get('active_id')
        analytic = self.env['account.analytic.account'].sudo().search([('state', '=', 'open'), ('id', '=', active_id)])
        for rec in analytic:
            for line in rec.rent_schedule_ids:
                if not line.is_created:
                    if line.start_date <= fields.Date.today():
                        line.create_invoice()
                        line.is_created = True
                        
                        
    def automatic_close_action(self):
        """Automatically close tenancy if all checks pass."""
        self.ensure_one()

        if not self.close_date:
            raise UserError(_("Please select a close date."))

        close_month = self.close_date.month
        close_year = self.close_date.year

        # Rent schedules in same month/year
        same_month_schedules = self.rent_schedule_ids.filtered(
            lambda r: r.start_date
            and r.start_date.month == close_month
            and r.start_date.year == close_year
        )

        # Block if any schedule not invoiced
        unposted_schedules = same_month_schedules.filtered(lambda r: not r.move_check)
        if unposted_schedules:
            raise UserError(_(
                "You cannot close this tenancy.\n"
                "Please create an invoice for the rent schedule(s) in %s %s before closing."
            ) % (self.close_date.strftime('%B'), self.close_date.year))

        # Block if any future rent schedules are invoiced
        future_schedules = self.rent_schedule_ids.filtered(
            lambda r: r.start_date and r.start_date > self.close_date
        )
        posted_schedules = future_schedules.filtered(lambda r: r.move_check)
        if posted_schedules:
            raise UserError(
                "You cannot close this tenancy because some future rent schedules are already invoiced/posted."
            )
        
        future_schedules = self.rent_schedule_ids.filtered(lambda r: r.start_date and r.start_date > self.close_date)
        future_schedules.unlink()
        # Delete any unposted schedules before close date
        # to_unlink = self.rent_schedule_ids.filtered(
        #     lambda r: not r.move_check and r.start_date and r.start_date < self.close_date
        # )
        # to_unlink.unlink()
        
        # Close the analytic account
        self.write({
            'state': 'close',
            'close_date': self.close_date,
        })

        # Post success message to chatter
        self.message_post(
            body=_("Tenancy automatically closed on %s.") % (self.close_date)
        )

        return True

    @api.model
    def _cron_automatic_close_action(self):
        """Cron job to automatically close tenancies on the close date."""
        today = fields.Date.today()
        analytic_accounts = self.sudo().search([
            ('close_date', '=', today),
            ('state', '!=', 'close'),
            ('state', '=', 'open'),
        ])
        for rec in analytic_accounts:
            try:
                rec.automatic_close_action()
                rec.message_post(
                    body=_(" Tenancy automatically closed successfully on %s.") % (today)
                )
            except Exception as e:
                # Post error message to chatter instead of _logger.error
                rec.message_post(
                    body=_(" Automatic closing failed: %s") % str(e)
                )
        return True
    
    # def _cron_automatic_close_action(self):
    #     analytic = self.env['account.analytic.account'].sudo().search([])
    #     for rec in analytic:
    #         if rec.close_date:
    #             if rec.close_date == fields.Date.today():
    #                 rec.button_close()
    #                 # rec.state = 'close'
