# See LICENSE file for full copyright and licensing details

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class AccountMoveLine(models.Model):
    _inherit ="account.move.line"
    
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
class AccountAnalyticAccount(models.Model):
    _name = "account.analytic.account"
    _description = 'Tenant Tenancy'
    _inherit = ["account.analytic.account", "mail.activity.mixin"]
    _order = 'code'

    @api.depends('total_credit_amt', 'total_debit_amt')
    def _compute_total_deb_cre_amt(self):
        """
        This method is used to calculate the total income amount by subtracting 
        total debit amount from total credit amount.
        """
        for tenancy in self:
            total = tenancy.total_credit_amt - tenancy.total_debit_amt
            tenancy.total_deb_cre_amt = total or 0.0

    @api.depends('account_move_line_ids.credit')
    def _compute_total_credit_amt(self):
        """
        This method calculates the total credit amount by summing the 'credit' 
        field values from the related account move lines.
        """
        for tenancy in self:
            tenancy.total_credit_amt = sum(line.credit for line in tenancy.account_move_line_ids) or 0.0


    @api.depends('account_move_line_ids.debit')
    def _compute_total_debit_amt(self):
        """
        Calculates the total debit amount for each tenancy by summing 
        the debit values from related account move lines.
        """
        for tenancy in self:
            tenancy.total_debit_amt = sum(line.debit for line in tenancy.account_move_line_ids) or 0.0

    @api.depends('rent_schedule_ids', 'rent_schedule_ids.amount')
    def _compute_total_rent(self):
        """
        This method is used to calculate Total Rent of current Tenancy.
        @param self: The object pointer
        @return: Calculated Total Rent.
        """
        for tenancy_brw in self:
            tenancy_brw.total_rent = sum(
                propety_brw.amount for propety_brw in
                tenancy_brw.rent_schedule_ids)

    @api.depends('deposit')
    def _compute_payment_type(self):
        """
        This method is used to set deposit return and deposit received
        boolean field accordingly to current Tenancy.
        @param self: The object pointer
        """
        self.deposit_received = False
        for tennancy in self:
            for payment in self.env['account.payment'].search(
                    [('tenancy_id', '=', tennancy.id),
                     ('state', '=', 'posted')]):
                if payment.payment_type == 'inbound':
                    tennancy.deposit_received = True

    @api.depends('prop_ids', 'multi_prop')
    def _total_prop_rent(self):
        """
        This method calculate total rent of all the selected property.
        @param self: The object pointer
        """
        self.ensure_one()
        if self._context.get('is_landlord_rent'):
            prop_val = self.prop_ids.ground_rent or 0.0
        else:
            prop_val = self.property_id.ground_rent or 0.0
        for pro_record in self:
            if pro_record.multi_prop:
                total = sum(prope_ids.ground for prope_ids
                            in pro_record.prop_ids)
                pro_record.rent = total + prop_val
            else:
                pro_record.rent = prop_val
                
    @api.model
    def default_get(self, fields):
        res = super(AccountAnalyticAccount, self).default_get(fields)
        if res.get('date_start'):
            res.update({'date': res['date_start'] + relativedelta(years=1)})
        return res
        
    plan_id = fields.Many2one(
        comodel_name='account.analytic.plan',
        string='Analytic Plan')
     
    contract_attachment = fields.Binary(
        string='Tenancy Contract',
        help='Contract document attachment for selected property')
    is_property = fields.Boolean(
        string='Is Property?')
    resident_type = fields.Selection(
        [('tenant_tenancy', 'Tenant Tenancy')], string="Resident Type")
    rent_entry_chck = fields.Boolean(
        string='Rent Entries Check',
        default=False)
    deposit_received = fields.Boolean(
        string='Deposit Received?',
        default=False,
        compute='_compute_payment_type',
        copy=False,
        help="True if deposit amount received for current Tenancy.")
    deposit_return = fields.Boolean(
        string='Deposit Returned?',
        default=False,
        type='boolean',
        compute='compute_amount_return',
        copy=False,
        help="True if deposit amount returned for current Tenancy.")
    code = fields.Char(
        string='Reference',
        default="/")
    doc_name = fields.Char(
        string='Filename')
    date = fields.Date(
        string='Expiration Date',
        index=True,
        help="Tenancy contract end date.")
    date_start = fields.Date(
        string='Start Date',
        default=fields.Date.context_today,
        help="Tenancy contract start date .")
    ten_date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        index=True,
        help="Tenancy contract creation date.")
    amount_fee_paid = fields.Integer(
        string='Amount of Fee Paid')
    manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Account Manager',
        help="Manager of Tenancy.")
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        domain="[('is_property','=', True)]",
        copy=False,
        help="Name of Property.")
    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Tenant',
        domain="[('tenant', '=', True)]",
        help="Tenant Name of Tenancy.")
    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        help="Contact person name.")
    rent_schedule_ids = fields.One2many(
        comodel_name='tenancy.rent.schedule',
        inverse_name='tenancy_id',
        string='Rent Schedule')
    account_move_line_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='analytic_account_id',
        string='Entries',)
        # readonly=True,
        # states={'draft': [('readonly', False)]})
    rent = fields.Monetary(
        string='Tenancy Rent',
        default=0.0,
        currency_field='currency_id',
        help="Tenancy rent for selected property per Month.")
    deposit = fields.Monetary(
        string='Deposit',
        default=0.0,
        currency_field='currency_id',
        copy=False,
        help="Deposit amount for tenancy.")
    total_rent = fields.Monetary(
        string='Total Rent',
        store=True,
        readonly=True,
        currency_field='currency_id',
        compute='_compute_total_rent',
        help='Total rent of this Tenancy.')
    amount_return = fields.Monetary(
        string='Deposit Returned',
        default=0.0,
        currency_field='currency_id',
        copy=False,
        help="Deposit Returned amount for Tenancy.")
    total_debit_amt = fields.Monetary(
        string='Total Debit Amount',
        default=0.0,
        compute='_compute_total_debit_amt',
        currency_field='currency_id')
    total_credit_amt = fields.Monetary(
        string='Total Credit Amount',
        default=0.0,
        compute='_compute_total_credit_amt',
        currency_field='currency_id')
    total_deb_cre_amt = fields.Monetary(
        string='Total Expenditure',
        default=0.0,
        compute='_compute_total_deb_cre_amt',
        currency_field='currency_id')
    description = fields.Text(
        string='Description',
        help='Additional Terms and Conditions')
    duration_cover = fields.Text(
        string='Duration of Cover',
        help='Additional Notes')
    acc_pay_dep_rec_id = fields.Many2one(
        comodel_name='account.payment',
        string='Account Payment',
        copy=False,
        help="Manager of Tenancy.")
    acc_pay_dep_ret_id = fields.Many2one(
        comodel_name='account.payment',
        string='Tenancy Manager',
        copy=False,
        help="Manager of Tenancy.")
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type')
    deposit_scheme_type = fields.Selection(
        [('insurance', 'Insurance-based')],
        'Type of Scheme')
    state = fields.Selection(
        [('template', 'Template'),
         ('draft', 'New'),
         ('book', 'Booked'),
         ('open', 'In Progress'),
         ('pending', 'To Renew'),
         ('close', 'Closed'),
         ('blocked', 'Blocked'),
         ('cancelled', 'Cancelled')],
        string='Status',
        required=True,
        copy=False,
        default='draft')
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        copy=False,
        string='Invoice')
    multi_prop = fields.Boolean(
        string='Multiple Property',
        help="Check this box Multiple property.")
    penalty_a = fields.Boolean(
        'Penalty')
    recurring = fields.Boolean(
        'Recurring')
    main_cost = fields.Float(
        string='Maintenance Cost',
        default=0.0,
        help="Insert maintenance cost")
    tenancy_cancelled = fields.Boolean(
        string='Tanency Cancelled',
        default=False)

    @api.constrains('date_start', 'date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Exiration date.
        @param self : object pointer
        """
        for rec in self:
            if rec.date_start and rec.date:
                if rec.date < rec.date_start:
                    raise ValidationError(
                        _('Expiration date should be grater then Start Date!'))

    @api.constrains('rent', 'deposit')
    def check_rent_positive(self):
        """
        This is a constraint method used to check the from date smaller than
        the Exiration date.
        @param self : object pointer
        """
        for rec in self:
            if rec.rent < 0:
                raise ValidationError(
                    _('Rent amount should be positive.'))
            if rec.deposit < 0:
                raise ValidationError(
                    _('Deposit amount should be positive.'))

    @api.model
    def create(self, vals):
        """
        This Method is used to overrides orm create method,
        to change state and tenant of related property.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        # if 'resident_type' in vals:
        vals['code'] = self.env['ir.sequence'].next_by_code(
            'account.analytic.account')
            # vals.update({'is_property': True})
        if 'property_id' in vals:
            prop_brw = self.env['account.asset'].browse(
                vals['property_id'])
            if vals.get('resident_type') == 'tenant_tenancy':
                prop_brw.write(
                    {'current_tenant_id': vals.get('tenant_id', False),
                     'state': 'book'})
        return super(AccountAnalyticAccount, self).create(vals)

    def write(self, vals):
        """
        This Method is used to overrides orm write method,
        to change state and tenant of related property.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        rec = super(AccountAnalyticAccount, self).write(vals)
        for tenancy_rec in self:
            if tenancy_rec.resident_type == 'tenant_tenancy' and vals.get('state') in ['open', 'close']:
                state_dict = {
                    'open': {'current_tenant_id': tenancy_rec.tenant_id.id, 'state': 'normal'},
                    'close': {'state': 'draft', 'current_tenant_id': False}
                    }
                tenancy_rec.property_id.write(state_dict.get(vals.get('state')))
        return rec

    def unlink(self):
        """
        Overrides orm unlink method,
        @param self: The object pointer
        @return: True/False.
        """
        analytic_line_obj = self.env['account.analytic.line']
        rent_schedule_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            if tenancy_rec.state not in ('draft', 'cancelled'):
                state_description_values = {
                    elem[0]: elem[1] for elem in
                    self._fields['state']._description_selection(self.env)}
                raise UserError(_(
                    'You cannot delete a tenancy record which '
                    'is in "%s" state.') % (
                    state_description_values.get(tenancy_rec.state),))
            analytic_line_rec = analytic_line_obj.search(
                [('account_id', '=', tenancy_rec.id)])
            if analytic_line_rec and analytic_line_rec.ids:
                analytic_line_rec.unlink()
            rent_ids = rent_schedule_obj.search(
                [('tenancy_id', '=', tenancy_rec.id)])
            if any(rent.move_check for rent in rent_ids):
                raise ValidationError(
                    _('You cannot delete Tenancy record, if any related Rent \
                    Schedule entries are in posted.'))
            else:
                rent_ids.unlink()
            if tenancy_rec.property_id.property_manager and \
                    tenancy_rec.property_id.property_manager.id:
                releted_user = tenancy_rec.property_id.property_manager.id
                new_ids = self.env['res.users'].search(
                    [('partner_id', '=', releted_user)])
                if releted_user and new_ids and new_ids.ids:
                    new_ids.write(
                        {'tenant_ids': [(3, tenancy_rec.tenant_id.id)]})
            tenancy_rec.property_id.write(
                {'state': 'draft', 'current_tenant_id': False})
        return super(AccountAnalyticAccount, self).unlink()

    # @api.depends('amount_return')
    @api.depends('invoice_id', 'invoice_id.payment_state')
    def compute_amount_return(self):
        """
        When you change Deposit field value, this method will change
        amount_fee_paid field value accordingly.
        @param self: The object pointer
        """
        self.deposit_return = False
        for data in self:
            if data.invoice_id.payment_state == ['in_payment', 'paid']:
                data.deposit_return = True

    @api.onchange('date_start', 'property_id')
    def onchange_date_start(self):
        """
        This Method is used to set property related fields value,
        on change of date_start.
        @param self: The object pointer
        """
        if self.property_id:
            self.rent_type_id = self.property_id.rent_type_id.id
            self.rent = self.property_id.ground_rent or False

    def button_receive(self):
        """
        This button method is used to open the related
        account payment form view.
        @param self: The object pointer
        @return: Dictionary of values.
        """
        context = dict(self._context) or {}
        print("contextcontextbutton_receivebutton_receive", context)
        payment_id = False
        acc_pay_form = self.env.ref(
            'account.view_account_payment_form')
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        payment_obj = self.env['account.payment']
        payment_method_id = self.env.ref(
            'account.account_payment_method_manual_in')
        context.update({'close_after_process': True})
        for tenancy_rec in self:
            if tenancy_rec.acc_pay_dep_rec_id and \
                    tenancy_rec.acc_pay_dep_rec_id.id:
                return {
                    'view_type': 'form',
                    'view_id': acc_pay_form.id,
                    'view_mode': 'form',
                    'res_model': 'account.payment',
                    'res_id': tenancy_rec.acc_pay_dep_rec_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': context,
                }
            if tenancy_rec.deposit == 0.00:
                raise ValidationError(_('Please Enter Deposit amount.'))
            if tenancy_rec.deposit < 0.00:
                raise ValidationError(
                    _('The deposit amount must be strictly positive.'))
            vals = {
                'partner_id': tenancy_rec.tenant_id.parent_id.id,
                'partner_type': 'customer',
                'journal_id': account_jrnl_obj.id,
                'payment_type': 'inbound',
                'ref': 'Deposit Received',
                'tenancy_id': tenancy_rec.id,
                'amount': tenancy_rec.deposit,
                'property_id': tenancy_rec.property_id.id,
                'payment_method_id': payment_method_id.id
            }
            payment_id = payment_obj.with_context(context).create(vals)
        return {
            'view_mode': 'form',
            'view_id': acc_pay_form.id,
            'view_type': 'form',
            'res_id': payment_id and payment_id.id,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': '[]',
            'context': context,
        }

    def button_return(self):
        """
        This method create supplier invoice for returning deposite
        amount.
        -----------------------------------------------------------
        @param self: The object pointer
        """
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        invoice_obj = self.env['account.move']
        wiz_form_id = self.env.ref('account.view_move_form').id
        for rec in self:
            inv_line_values = {
                'name': _('Deposit Return') or "",
                # 'origin': 'account.analytic.account' or "",
                'quantity': 1,
                'account_id': rec.property_id.expense_account_id.id or False,
                'price_unit': rec.deposit or 0.00,
                # 'analytic_distribution': rec.id or False,
                'analytic_distribution': {rec.id : 100} if rec.id else {},
            }
            if rec.multi_prop:
                for data in rec.prop_ids:
                    if data.property_id and data.property_id.income_acc_id:
                        for account in data.property_id.income_acc_id:
                            account_id = account.id
                        inv_line_values.update({'account_id': account_id})
            inv_values = {
                # 'origin': _('Deposit Return For ') + rec.name or "",
                'move_type': 'in_invoice',
                'property_id': rec.property_id.id,
                'partner_id': rec.tenant_id.parent_id.id or False,
                # 'account_id':
                #     rec.tenant_id.parent_id.property_account_payable_id.id
                #         or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'invoice_date': fields.Date.context_today(self) or False,
                'new_tenancy_id': rec.id,
                # 'ref': rec.code,
                'journal_id':
                account_jrnl_obj and account_jrnl_obj.id or False,
            }
            acc_id = invoice_obj.create(inv_values)
            rec.write({'invoice_id': acc_id.id})
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': rec._context,
        }

    def button_open_recived(self):
        wiz_form_id = self.env.ref('account.view_move_form').id
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': self._context,
        }

    def button_book(self):
        """
        This button method is used to Change Tenancy state to book.
        @param self: The object pointer
        """
        for tenancy_rec in self:
            tenant_tenancy_rec = self.env['account.analytic.account'].search([('property_id', '=', tenancy_rec.property_id.id),('state', '=', 'draft')])
            if tenant_tenancy_rec and len(tenant_tenancy_rec) > 1:
                raise UserError(_(
                    'You cannot book a tenancy record which '
                    'is found in "%s" state.') % (
                    tenancy_rec.state))
            if tenancy_rec.tenant_id:
                prop_brw = self.env['account.asset'].browse(tenancy_rec.property_id.id)
                prop_brw.write(
                    {'current_tenant_id': tenancy_rec.tenant_id.id,
                     'state': 'book'})
        return self.write({'state': 'book'})

    def button_start(self):
        """
        This button method is used to Change Tenancy state to Open.
        @param self: The object pointer
        """
        user_obj = self.env['res.users']
        for current_rec in self:
            if current_rec.resident_type == 'tenant_tenancy':
                if current_rec.property_id.property_manager and \
                        current_rec.property_id.property_manager.id:
                    releted_user = current_rec.property_id.property_manager.id
                    new_ids = user_obj.search(
                        [('partner_id', '=', releted_user)])
                    if releted_user and new_ids and new_ids.ids:
                        new_ids.write(
                            {'tenant_ids': [(4, current_rec.tenant_id.id)]})
        return self.write({'state': 'open', 'rent_entry_chck': False})

    def button_close(self):
        """
        This button method is used to Change Tenancy state to close.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'close'})

    def button_set_to_draft(self):
        """
        This button method is used to Change Tenancy state to close.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({
                'state': 'draft',
                'rent_schedule_ids': [(2, rec.rent_schedule_ids.ids)]})

    def button_set_to_renew(self):
        """
        This Method is used to open Tenancy renew wizard.
        @param self: The object pointer
        @return: Dictionary of values.
        """
        self.ensure_one()
        rent_schedule_obj = self.env['tenancy.rent.schedule']
        for tenancy_brw in self:
            if rent_schedule_obj.search(
                [('tenancy_id', '=', tenancy_brw.id),
                 ('move_check', '=', False)]):
                raise ValidationError(
                    _('In order to Renew a Tenancy, Please make all '
                      'related Rent Schedule entries posted.'))
        return {
            'name': _('Tenancy Renew Wizard'),
            'res_model': 'renew.tenancy',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_start_date': self.date}
        }

    @api.model
    def cron_property_states_changed(self):
        """
        This Method is called by Scheduler for change property state
        according to tenancy state.
        @param self: The object pointer
        """
        current_date = fields.Date.context_today(self)
        tncy_rec = self.search([('date_start', '<=', current_date),
                                ('date', '>=', current_date),
                                ('state', '=', 'open'),
                                ('is_property', '=', True)])
        for tncy_data in tncy_rec:
            if tncy_data.property_id and tncy_data.property_id.id:
                tncy_data.property_id.write(
                    {'state': 'normal', 'color': 7})
        return True

    # @api.model
    # def cron_property_tenancy(self):
    #     """
    #     This Method is called by Scheduler to send email
    #     to tenant as a reminder for rent payment.
    #     @param self: The object pointer
    #     """
    #     due_date = fields.Date.context_today(self) + relativedelta(days=7)
    #     tncy_ids = self.search(
    #         [('resident_type', '=', 'tenant_tenancy'), ('state', '=', 'open')])
    #     rent_schedule_obj = self.env['tenancy.rent.schedule']
    #     model_data_id = self.env.ref(
    #         'property_management.property_email_template')
    #     for tncy_data in tncy_ids:
    #         tncy_rent_ids = rent_schedule_obj.search(
    #             [('tenancy_id', '=', tncy_data.id),
    #              ('start_date', '=', due_date)])
    #         for tenancy in tncy_rent_ids:
    #             model_data_id.send_mail(
    #                 tenancy.id, force_send=True, raise_exception=False)
    #     return True

    def create_rent_schedule(self):
        """
        This button method is used to create rent schedule Lines.
        @param self: The object pointer
        """
        rent_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            if tenancy_rec.rent_type_id.renttype == 'Weekly':
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                interval = int(tenancy_rec.rent_type_id.name)
                if d2 < d1:
                    raise ValidationError(
                        _('End date must be greater than start date.'))
                wek_diff = (d2 - d1)
                wek_tot1 = (wek_diff.days) / (interval * 7)
                wek_tot = (wek_diff.days) % (interval * 7)
                if wek_diff.days == 0:
                    wek_tot = 1
                if wek_tot1 > 0:
                    for wek_rec in range(int(wek_tot1)):
                        rent_obj.create(
                            {'start_date': d1,
                             'amount': tenancy_rec.rent * interval or 0.0,
                            #  'property_id': tenancy_rec.property_id
                            #     and tenancy_rec.property_id.id or False,
                            #  'tenancy_id': tenancy_rec.id,
                            #  'currency_id': tenancy_rec.currency_id.id
                            #     or False,
                            #  'rel_tenant_id': tenancy_rec.tenant_id.id
                            'property_id': tenancy_rec.property_id.id if tenancy_rec.property_id else False,
                             'tenancy_id': tenancy_rec.id,
                             'currency_id': tenancy_rec.currency_id.id if tenancy_rec.currency_id else False,
                             'rel_tenant_id': tenancy_rec.tenant_id.id if tenancy_rec.tenant_id else False,
                             })
                        d1 = d1 + relativedelta(days=(7 * interval))
                if wek_tot > 0:
                    one_day_rent = 0.0
                    if tenancy_rec.rent:
                        one_day_rent = (tenancy_rec.rent) / (7 * interval)
                    rent_obj.create(
                        {'start_date': d1.strftime(
                            DEFAULT_SERVER_DATE_FORMAT),
                         'amount': (one_day_rent * (wek_tot)) or 0.0,
                        #  'property_id': tenancy_rec.property_id
                        #     and tenancy_rec.property_id.id or False,
                        #  'tenancy_id': tenancy_rec.id,
                        #  'currency_id': tenancy_rec.currency_id.id or False,
                        #  'rel_tenant_id': tenancy_rec.tenant_id.id
                        'property_id': tenancy_rec.property_id.id if tenancy_rec.property_id else False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id if tenancy_rec.currency_id else False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id if tenancy_rec.tenant_id else False,
                         })
            elif tenancy_rec.rent_type_id.renttype != 'Weekly':
                if tenancy_rec.rent_type_id.renttype == 'Monthly':
                    interval = int(tenancy_rec.rent_type_id.name)
                if tenancy_rec.rent_type_id.renttype == 'Yearly':
                    interval = int(tenancy_rec.rent_type_id.name) * 12
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                diff = abs((d1.year - d2.year) * 12 + (d1.month - d2.month))
                tot_rec = diff / interval
                tot_rec2 = diff % interval
                if abs(d1.month - d2.month) >= 0 and d1.day < d2.day:
                    tot_rec2 += 1
                if diff == 0:
                    tot_rec2 = 1
                if tot_rec > 0:
                    for rec in range(int(tot_rec)):
                        rent_obj.create(
                            {'start_date': d1,
                             'amount': tenancy_rec.rent * interval or 0.0,
                             'property_id': tenancy_rec.property_id.id if tenancy_rec.property_id else False,
                             'tenancy_id': tenancy_rec.id,
                             'currency_id': tenancy_rec.currency_id.id if tenancy_rec.currency_id else False,
                             'rel_tenant_id': tenancy_rec.tenant_id.id if tenancy_rec.tenant_id else False,
                             })
                        d1 = d1 + relativedelta(months=interval, day=tenancy_rec.date_start.day)
                if tot_rec2 > 0:
                    rent_obj.create({
                        'start_date': d1,
                        'amount': tenancy_rec.rent * interval or 0.0,
                        'property_id': tenancy_rec.property_id.id if tenancy_rec.property_id else False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id if tenancy_rec.currency_id else False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id if tenancy_rec.tenant_id else False,
                    })
                    # rent_obj.create({
                    #     'start_date': d1,
                    #     'amount': tenancy_rec.rent * tot_rec2 or 0.0,
                    #     'property_id': tenancy_rec.property_id
                    #     and tenancy_rec.property_id.id or False,
                    #     'tenancy_id': tenancy_rec.id,
                    #     'currency_id': tenancy_rec.currency_id.id or False,
                    #     'rel_tenant_id': tenancy_rec.tenant_id.id
                    # })
            return tenancy_rec.write({'rent_entry_chck': True})

    def button_cancel_tenancy(self):
        """
        This button method is used to Change Tenancy state to Cancelled.
        @param self: The object pointer
        """
        for record in self:
            record.write(
                {'state': 'cancelled', 'tenancy_cancelled': True})
            record.property_id.write(
                {'state': 'draft'})
            rent_ids = self.env['tenancy.rent.schedule'].search(
                [('tenancy_id', '=', record.id),
                 ('paid', '=', False),
                 ('move_check', '=', False)])
            for value in rent_ids:
                value.write({'is_readonly': True})
        return True
