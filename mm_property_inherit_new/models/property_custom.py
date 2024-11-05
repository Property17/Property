from num2words import num2words
from .money_to_text_ar import amount_to_text_arabic
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime
from datetime import date, datetime, time
from odoo.exceptions import UserError, ValidationError
# test

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
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', related='tenancy_id.analytic_account_id', store=True)
    cheque_detail = fields.Char(string='Cheque Detail',)
    rent_residual = fields.Monetary(string='Pending Amount', currency_field='currency_id',)
    note = fields.Text(string='Notes')

    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
            ('blocked', 'Blocked'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    state_ch = fields.Char()
    run_comp = fields.Boolean('Run Comp')
    # run_comp = fields.Boolean(compute='_compute_analytic_account')

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

    def action_create_payments(self):
        active_id = self._context.get('active_ids') or self._context.get('active_id')
        account_move = self.env['account.move'].search([('id', '=', active_id)])
        tenancy_rent = self.env['tenancy.rent.schedule'].search(
            [('tenancy_id', '=', account_move.tenancy_id.id), ('start_date', '<=', account_move.invoice_date)])
        if tenancy_rent:
            for line in tenancy_rent:
                if not line.paid:
                    if line.invoice_id.id != account_move.id:
                        raise UserError(
                            _('You cannot paid this entry please paid this entry first: %s ') % (line.invoice_id.name,))
                    else:
                        account_move.user_paid_by_id = self.env.user.id
                        account_move.mm_journal_id = self.journal_id.id
                        account_move.paid_date = self.payment_date

                        payments = self._create_payments()

                        if self._context.get('dont_redirect_to_payments'):
                            return True
                        action = {
                            'name': _('Payments'),
                            'type': 'ir.actions.act_window',
                            'res_model': 'account.payment',
                            'context': {'create': False},
                        }
                        if len(payments) == 1:
                            action.update({
                                'view_mode': 'form',
                                'res_id': payments.id,
                            })
                            pay = self.env['account.payment'].search([('id', '=', payments.id)])
                            if pay.move_id:
                                pay.move_id._compute_analytic_account()

                        else:
                            action.update({
                                'view_mode': 'tree,form',
                                'domain': [('id', 'in', payments.ids)],
                            })
                            pay2 = self.env['account.payment'].search([('id', 'in', payments.ids)])
                            for p in pay2:
                                if p.move_id:
                                    p.move_id._compute_analytic_account()
                        return action
        else:
            account_move.user_paid_by_id = self.env.user.id
            account_move.mm_journal_id = self.journal_id.id
            account_move.paid_date = self.payment_date

            payments = self._create_payments()

            if self._context.get('dont_redirect_to_payments'):
                return True

            action = {
                'name': _('Payments'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'context': {'create': False},
            }
            if len(payments) == 1:
                action.update({
                    'view_mode': 'form',
                    'res_id': payments.id,
                })
                pay = self.env['account.payment'].search([('id', '=', payments.id)])
                if pay.move_id:
                    pay.move_id._compute_analytic_account()

            else:
                action.update({
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', payments.ids)],
                })
                pay2 = self.env['account.payment'].search([('id', 'in', payments.ids)])
                for p in pay2:
                    if p.move_id:
                        p.move_id._compute_analytic_account()
            return action


    def _create_payment_vals_from_wizard(self):
        active_id = self._context.get('active_ids') or self._context.get('active_id')
        account_move = self.env['account.move'].search([('id', '=', active_id)])
        res = super()._create_payment_vals_from_wizard()
        res.update({'tenancy_id': account_move.tenancy_id.id if account_move.tenancy_id.id else False,})
        return res


class AccountAssetAssetNew(models.Model):
    _inherit = "account.asset"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    auto_add_no = fields.Char(string='Auto - Address No ')

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for rec in self:
            if rec.parent_id:
                rec.analytic_account_id = rec.parent_id.analytic_account_id.id


class AccountPaymentInhNew(models.Model):
    _inherit = "account.payment"

    date_ch = fields.Char(compute='_compute_get_date')
    mm_invoice_id = fields.Many2one('account.move', string="Invoice")

    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)


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

    def get_invloice_lines(self):
        """TO GET THE INVOICE LINES"""
        inv_line = {}
        for rec in self:
            inv_line = {
                # 'origin': 'tenancy.rent.schedule',
                'name': _('Tenancy(Rent) Cost'),
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'account_id': rec.tenancy_id.property_id.income_acc_id.id or False,
                # 'analytic_distribution': rec.tenancy_id.id or False,
                'analytic_distribution': {rec.tenancy_id.id : 100} if rec.tenancy_id else {},

            }
        return [(0, 0, inv_line)]

    def create_invoice(self):
        """
        Create invoice for Rent Schedule.
        @param self: The object pointer
        """
        inv_obj = self.env['account.move']
        for rec in self:
            inv_line_values = rec.get_invloice_lines()
            print("inv_line_values", inv_line_values)
            inv_values = {
                'partner_id': rec.tenancy_id.tenant_id.parent_id.id or False,
                'move_type': 'out_invoice',
                'property_id': rec.tenancy_id.property_id.id or False,
                'tenancy_id': rec.tenancy_id.id or False,
                'invoice_date': rec.start_date or False,
                'cheque_detail': rec.cheque_detail or False,
                'rent_residual': rec.rent_residual or False,
                'note': rec.note or False,
                'invoice_line_ids': inv_line_values,
                'new_tenancy_id': rec.tenancy_id.id,
                'auto_post': 'at_date'
            }
            print("inv_values", inv_values)
            invoice_id = inv_obj.with_company(rec.company_id.id).create(inv_values)
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


class AccountAnalyticAccountNew(models.Model):
    _inherit = "account.analytic.account"

    legal_type_id = fields.Many2one('legal.type', string='Legal Type', )
    activity_type_lo_id = fields.Many2one('activity.type', string='Activity Type', )
    property_manager_id = fields.Many2one(comodel_name='res.partner', string='Property Manager')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
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

    def _compute_run_func(self):
        for rec in self:
            rec.run_comp = True
            rec._compute_total_rent()

    @api.depends('rent_schedule_ids', 'rent', 'rent_type_id')
    def _compute_total_rent(self):
        """
        This method is used to calculate Total Rent of current Tenancy.
        @param self: The object pointer
        @return: Calculated Total Rent.
        """
        for tenancy_brw in self:
            tenancy_brw.total_rent = 0
            if tenancy_brw.rent_type_id.renttype == 'Monthly':
                tenancy_brw.total_rent = tenancy_brw.rent * int(tenancy_brw.rent_type_id.name)
            if tenancy_brw.rent_type_id.renttype == 'Yearly':
                tenancy_brw.total_rent = tenancy_brw.rent * (int(tenancy_brw.rent_type_id.name) * 12)
            if tenancy_brw.rent_type_id.renttype == 'Weekly':
                tenancy_brw.total_rent = tenancy_brw.rent * (int(tenancy_brw.rent_type_id.name) / 4)

    def name_get(self):
        res = []
        for analytic in self:
            name = analytic.name
            if analytic.code:
                name = analytic.code
            res.append((analytic.id, name))
        return res

    def button_close(self):
        """
        This button method is used to Change Tenancy state to close.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'close'})
            rec.close_date = fields.Date.today()

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
                rec.analytic_account_id = rec.property_id.analytic_account_id.id

    @api.onchange('property_manager_id')
    def domain_property_id(self):
        self.property_id = False
        self.analytic_account_id = False
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

    def _cron_automatic_close_action(self):
        analytic = self.env['account.analytic.account'].sudo().search([])
        for rec in analytic:
            if rec.close_date:
                if rec.close_date == fields.Date.today():
                    rec.state = 'close'
