# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Account Entry"

    # asset_id = fields.Many2one(
    #     comodel_name='account.asset',
    #     help='Asset')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        help='Property Name.')
    new_tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy ')
    schedule_date = fields.Date(
        string='Schedule Date',
        help='Rent Schedule Date.')
    source = fields.Char(
        string='Account Source',
        help='Source from where account move created.')
    payment_journal_id = fields.Many2one('account.journal', string="Payment Journal")
    payment_method_line_id = fields.Many2one('account.payment.method.line', string="Payment Method")
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.'
    )
   

    def assert_balanced(self):
        prec = self.env['decimal.precision'].precision_get('Account')
        if self.ids:
            self._cr.execute("""
                SELECT move_id FROM account_move_line WHERE move_id in %s
                GROUP BY move_id HAVING abs(sum(debit) - sum(credit)) > %s
                """, (tuple(self.ids), 10 ** (-max(5, prec))))
            if self._cr.fetchall():
                raise UserError(_("Cannot create unbalanced journal entry."))
        return True
    
    # @api.model
    # def create(self, vals):
    #     move = super(AccountMove, self).create(vals)
    #     move._set_analytic_account_on_counterpart_lines()
    #     return move

    # def write(self, vals):
    #     res = super(AccountMove, self).write(vals)
    #     self._set_analytic_account_on_counterpart_lines()
    #     return res

    # def _set_analytic_account_on_counterpart_lines(self):
    #     """
    #     Ensure `analytic_account_id` is set on both debit and credit lines within the same move.
    #     """
    #     for move in self:
    #         debit_lines = move.line_ids.filtered(lambda line: line.debit > 0 and line.analytic_account_id)
    #         print("**************************************debit_lines", debit_lines)
    #         for debit_line in debit_lines:
    #             print("**************************************debit_lines", debit_lines)
    #             # Find corresponding credit lines without an `analytic_account_id`
    #             credit_lines = move.line_ids.filtered(lambda line: line.credit > 0 and not line.analytic_account_id)
    #             print("**************************************credit_lines", credit_lines)

    #             for credit_line in credit_lines:
    #                 credit_line.analytic_account_id = debit_line.analytic_account_id
    #                 print("**************************************credit_line", credit_line)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property', 
        help='Property Name.')
    
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
   
    # invoice_id = fields.Many2one('account.move', related='move_id.invoice_id', string="Invoice")
    
    
    
    # def action_register_payment(self):
    #     ''' Open the account.payment.register wizard to pay the selected journal items.
    #     :return: An action opening the account.payment.register wizard.
    #     '''
    #     return {
    #         'name': _('Register Payment'),
    #         'res_model': 'account.payment.register',
    #         'view_mode': 'form',
    #         'views': [[False, 'form']],
    #         'context': {
    #             'active_model': 'account.move.line',
    #             'active_ids': self.ids,
    #             # 'default_tenancy_id': self.tenancy_id.id,
    #             # 'default_property_id': self.property_id.id,
    #             # 'default_invoice_id': self.move_id.id,
    #         },
    #         'target': 'new',
    #         'type': 'ir.actions.act_window',
    #     }

    
    # def action_register_payment(self):
    #     ''' Open the account.payment.register wizard to pay the selected journal items.
    #     :return: An action opening the account.payment.register wizard.
    #     '''
    #     return {
    #         'name': _('Register Payment'),
    #         'res_model': 'account.payment.register',
    #         'view_mode': 'form',
    #         'views': [[False, 'form']],
    #         'context': {
    #             'active_model': 'account.move.line',
    #             'active_ids': self.ids,
    #         },
    #         'target': 'new',
    #         'type': 'ir.actions.act_window',
    #     }
        
    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal items.
        :return: An action opening the account.payment.register wizard.
        '''
        # Ensure that the method can handle multiple records
        tenancy_ids = self.mapped('move_id.tenancy_id.id')
        property_ids = self.mapped('move_id.property_id.id')
        invoice_ids = self.mapped('move_id.id')

        # If there are conflicting values, you need to decide how to handle them.
        # For simplicity, we can raise an error if the selected records belong to different tenancies or properties.
        # if len(set(tenancy_ids)) > 1:
        #     raise UserError("Selected records are associated with different tenancies. Please select records with the same tenancy.")
        # if len(set(property_ids)) > 1:
        #     raise UserError("Selected records are associated with different properties. Please select records with the same property.")

        # Use the first tenancy and property for the default values
        default_tenancy_id = tenancy_ids[0] if tenancy_ids else False
        default_property_id = property_ids[0] if property_ids else False
        default_invoice_id = invoice_ids[0] if invoice_ids else False
        
        # for record in self:
        #     if record.invoice_id:
        #         # Update payment_journal_id with the journal_id
        #         record.move_id.invoice_id.payment_journal_id = record.journal_id.id
        #         # Update paid_date with the date
        #         record.move_id.invoice_id.paid_date = record.payment_date
        #         record.move_id.invoice_id.payment_method_line_id = record.payment_method_line_id.id

        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'context': {
                'active_model': 'account.move.line',
                'active_ids': self.ids,
                'default_tenancy_id': default_tenancy_id,
                # 'default_property_id': default_property_id,
                # 'default_invoice_id': default_invoice_id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        help='Property Name.')
    invoice_id = fields.Many2one('account.move',string="Invoice")

    
    @api.model
    def default_get(self, fields_list):
        res = super(AccountPaymentRegister, self).default_get(fields_list)
        context = self.env.context
        invoice_obj = self.env['account.move']
        if self._context.get('active_id'):
            invoice_id = invoice_obj.browse(context['active_id'])
            res['property_id'] = invoice_id.property_id.id
            res['invoice_id'] = invoice_id.id
            
        return res
    
    
    def _create_payment_vals_from_batch(self, batch_result):
        batch_values = self._get_wizard_values_from_batch(batch_result)

        if batch_values['payment_type'] == 'inbound':
            partner_bank_id = self.journal_id.bank_account_id.id
        else:
            partner_bank_id = batch_result['payment_values']['partner_bank_id']

        payment_method_line = self.payment_method_line_id

        if batch_values['payment_type'] != payment_method_line.payment_type:
            payment_method_line = self.journal_id._get_available_payment_method_lines(batch_values['payment_type'])[:1]

        payment_vals = {
            'date': self.payment_date,
            'amount': batch_values['source_amount_currency'],
            'payment_type': batch_values['payment_type'],
            'partner_type': batch_values['partner_type'],
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': batch_values['source_currency_id'],
            'partner_id': batch_values['partner_id'],
            'partner_bank_id': partner_bank_id,
            'payment_method_line_id': payment_method_line.id,
            'destination_account_id': batch_result['lines'][0].account_id.id,
            'write_off_line_vals': [],
        }

        total_amount, mode = self._get_total_amount_using_same_currency(batch_result)
        currency = self.env['res.currency'].browse(batch_values['source_currency_id'])
        if mode == 'early_payment':
            payment_vals['amount'] = total_amount

            epd_aml_values_list = []
            for aml in batch_result['lines']:
                if aml.move_id._is_eligible_for_early_payment_discount(currency, self.payment_date):
                    epd_aml_values_list.append({
                        'aml': aml,
                        'amount_currency': -aml.amount_residual_currency,
                        'balance': currency._convert(-aml.amount_residual_currency, aml.company_currency_id, self.company_id, self.payment_date),
                    })

            open_amount_currency = (batch_values['source_amount_currency'] - total_amount) * (-1 if batch_values['payment_type'] == 'outbound' else 1)
            open_balance = currency._convert(open_amount_currency, aml.company_currency_id, self.company_id, self.payment_date)
            early_payment_values = self.env['account.move']\
                ._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list, open_balance)
            for aml_values_list in early_payment_values.values():
                payment_vals['write_off_line_vals'] += aml_values_list

        return payment_vals
    
    
    def _create_payments(self):
        
        """Override to add logic for updating payment_journal_id and paid_date."""
        result = super(AccountPaymentRegister, self)._create_payments()
        # Update the related `account.move` record
        for record in self:
            if record.invoice_id:
                # Update payment_journal_id with the journal_id
                record.invoice_id.payment_journal_id = record.journal_id.id
                # Update paid_date with the date
                record.invoice_id.paid_date = record.payment_date
                record.invoice_id.payment_method_line_id = record.payment_method_line_id.id
                record.invoice_id.invoice_user_id = self.env.user.id
                record.invoice_id.payment_reference = record.communication
                # record.mm_move_id

        return result    
     
        

    # @api.model
    # def default_get(self, fields_list):
    #     # OVERRIDE
    #     res = super().default_get(fields_list)
    #     context = dict(self._context) or {}
    #     active_id = self.env[context.get('active_model')].browse(
    #         context.get('active_id'))
    #     if active_id:
    #         res['property_id'] = active_id.property_id.id or False
    #         # res['tenancy_id'] = active_id.new_tenancy_id.id or False
    #     return res

    # def _create_payment_vals_from_wizard(self):
    #     res = super()._create_payment_vals_from_wizard()
    #     res.update({'property_id': self.property_id.id})
    #     return res
    
    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        payment_vals['property_id'] = self.property_id.id
        payment_vals['mm_move_id'] = self.invoice_id.id
        return payment_vals 


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # tenancy_id = fields.Many2one(
    #     comodel_name='account.analytic.account',
    #     string='Tenancy', related='mm_move_id.tenancy_id', store=True,
    #     help='Tenancy Name.')
    # property_id = fields.Many2one(
    #     comodel_name='account.asset', store=True,
    #     string='Property',  related='mm_move_id.property_id',
    #     help='Property Name.')
    
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy', store=True,
        help='Tenancy Name.')
    property_id = fields.Many2one(
        comodel_name='account.asset', store=True,
        string='Property',
        help='Property Name.')
    
    
    amount_due = fields.Monetary(
        comodel_name='res.partner',
        related='partner_id.credit',
        readonly=True,
        help='Display Due amount of Customer')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
   
    properitis = fields.Text(
        string='Properties',
        help="Multiple property.", compute="_compute_properitis",
        store=True)
    
    mm_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice2',
        help='Select the related invoice.',
        compute="compute_mm_move_id"
    )
    mm_invoice_id = fields.Many2one('account.move', string="Invoice")

    
    @api.depends('mm_invoice_id')
    def compute_mm_move_id(self):
        for rec in self:
            if rec.mm_invoice_id:
                rec.mm_move_id = rec.mm_invoice_id.id
                rec._onchange_mm_move_id()
            else:
                rec.mm_move_id = False
                
    # @api.onchange('mm_invoice_id')
    # def _onchange_mm_invoice_id(self):
    #     for rec in self:
    #         if rec.mm_invoice_id:
    #             rec.mm_move_id = rec.mm_invoice_id.id
    #             rec._onchange_mm_move_id()
    #         else:
    #             rec.mm_move_id = False
            
    def update_mm_move_id(self):
        for rec in self:
            if rec.mm_invoice_id and not rec.mm_move_id:
                rec.mm_move_id = rec.mm_invoice_id.id
            else:
                rec.mm_move_id = False
    
    
    # @api.depends('mm_invoice_id')
    # def update_mm_move_id(self):
    #     if self.mm_invoice_id and not self.mm_move_id:
    #         self.mm_move_id = self.mm_invoice_id.id
    #     else:
    #         self.mm_move_id  = False
    
    @api.onchange('mm_move_id')
    def _onchange_mm_move_id(self):
        """
        Automatically set tenancy_id and property_id based on the selected mm_move_id (invoice).
        """
        if self.mm_move_id:
            self.tenancy_id = self.mm_move_id.tenancy_id
            self.property_id = self.mm_move_id.property_id
            self.mm_move_id.paid_date = self.date
            self.mm_move_id.payment_method_line_id = self.payment_method_line_id.id
            self.mm_move_id.payment_journal_id = self.journal_id.id
            self.mm_move_id.invoice_user_id = self.user_id.id
            self.mm_move_id.payment_reference = self.ref
        else:
            self.tenancy_id = False
            self.property_id = False

    # @api.onchange('mm_move_id')
    # def _onchange_mm_move_id(self):
    #     print("**************************88", self.tenancy_id)
    #     if self.mm_move_id:
    #         # _logger.info(f"Setting tenancy_id: {self.mm_move_id.tenancy_id}, property_id: {self.mm_move_id.property_id}")
    #         self.tenancy_id = self.mm_move_id.tenancy_id
    #         self.property_id = self.mm_move_id.property_id
    #         print("**************************88", self.tenancy_id)
    #     else:
    #         # _logger.info("Resetting tenancy_id and property_id to False.")
    #         self.tenancy_id = False
    #         self.property_id = False
    
    # @api.onchange('mm_move_id')
    # def _onchange_mm_move_id(self):
    #     """
    #     Automatically set tenancy_id and property_id based on the selected mm_move_id (invoice).
    #     """
    #     if self.mm_move_id:
    #         self.tenancy_id = self.mm_move_id.tenancy_id or False
    #         self.property_id = self.mm_move_id.property_id or False
    #     else:
    #         pass
            # self.tenancy_id = False
            # self.property_id = False
    
    # @api.model
    # def create(self, vals):
    #     # Check if tenancy_id or property_id are missing
    #     if not vals.get('tenancy_id') or not vals.get('property_id'):
    #         if vals.get('mm_move_id'):  
    #             invoice = self.env['account.move'].browse(vals['mm_move_id'])
    #             if not vals.get('tenancy_id') and invoice.tenancy_id:
    #                 vals['tenancy_id'] = invoice.tenancy_id.id
    #             if not vals.get('property_id') and invoice.property_id:
    #                 vals['property_id'] = invoice.property_id.id
        
    #     return super(AccountPayment, self).create(vals)
    
    @api.depends('tenancy_id.multi_properitis')
    def _compute_properitis(self):
        for record in self:
            if record.tenancy_id:
                record.properitis = record.tenancy_id.multi_properitis
            else:
                record.properitis = False
    
    @api.onchange('tenancy_id')
    def _onchange_tenancy_id(self):
        """
        Automatically set the property_id based on the selected tenancy_id.
        """
        if self.tenancy_id:
            self.property_id = self.tenancy_id.property_id
        else:
            self.property_id = False

    
    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        for rec in self:
            if rec.tenancy_id and rec.is_deposit_receive:
                rec.tenancy_id.deposit_received = False
        return res

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        invoice_obj = self.env['account.move']
        context = dict(self._context or {})
        for rec in self:
            if context.get('return'):
                invoice_browse = invoice_obj.browse(
                    context.get('active_id')).new_tenancy_id
                invoice_browse.write({'amount_return': rec.amount})
            if context.get('deposite_received'):
                tenancy_active_id = \
                    self.env['account.analytic.account'].browse(
                        context.get('active_id'))
                tenancy_active_id.write({'amount_return': rec.amount})
            if rec.tenancy_id and rec.is_deposit_receive:
                rec.tenancy_id.deposit_received = True
        return res

    # @api.model
    # def create(self, vals):
    #     res = super(AccountPayment, self).create(vals)
    #     if res and res.id and res.tenancy_id and res.tenancy_id.id:
    #         if res.payment_type == 'inbound':
    #             res.tenancy_id.write({'acc_pay_dep_rec_id': res.id})
    #         if res.payment_type == 'outbound':
    #             res.tenancy_id.write({'acc_pay_dep_ret_id': res.id})
    #     return res
    
    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=False, **kwargs):
        """Override to add analytic account to journal items during payment."""
        # Call the super method
        result = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals, **kwargs)
        # Handle context-specific properties (like 'property_id')
        context = dict(self._context or {})
        if context.get('account_deposit_received'):
            for line in result:
                if line.get('debit') > 0 and self.tenancy_id.id:
                    if self.payment_type in ('inbound', 'outbound'):
                        line.update({
                            'property_id': self.property_id.id
                        })

        # Return the final result
        return result

    
    # def _prepare_move_line_default_vals(self, write_off_line_vals=None):
    #     result = super()._prepare_move_line_default_vals(write_off_line_vals)
    #     context = dict(self._context or {})
    #     print("contextcontextcontextcontext", context)
    #     for line in result:
    #         if not self.move_id.property_id:
    #             self.move_id.property_id = self.property_id.id or False
    #         if context.get('account_deposit_received') and line.get('debit') > 0 and self.tenancy_id.id:
    #             if self.payment_type in ('inbound', 'outbound'):
    #                 line.update({
    #                     'property_id': self.property_id.id
    #                 })
    #                 print("contextcontextcontextcontextlineline", line)
    #     return result


    # def _prepare_move_line_default_vals(self, write_off_line_vals):
    #     result = super()._prepare_move_line_default_vals(write_off_line_vals)
    #     context = dict(self._context) or {}
    #     for line in result:
    #         if not self.move_id.property_id:
    #             self.move_id.property_id = self.property_id.id or False
    #         if context.get('account_deposit_received') and line.get('debit') > 0 and self.tenancy_id.id:
    #             if self.payment_type in ('inbound', 'outbound'):
    #                 line.update({
    #                     # 'analytic_account_id': self.tenancy_id.id,
    #                     'property_id': self.property_id.id
    #                     })
    #     return result
    

    def _seek_for_lines(self):
        rec = super(AccountPayment, self)._seek_for_lines()
        if rec and rec[0] and self.tenancy_id and self.tenancy_id.id:
            if self.payment_type in ('inbound', 'outbound'):
                rec[0].update({'property_id': self.property_id.id})
                # rec[0].update({'analytic_account_id': self.tenancy_id.id, 'property_id': self.property_id.id})
        return rec

    
    # @api.model_create_multi
    # def create(self, vals_list):
    #     records = super().create(vals_list)
    #     for rec in records:
    #         print("*************************************************")
    #         # Run your custom update_mm_move_id logic
    #         rec.update_mm_move_id()
    #         # Instead of calling onchange, set fields directly
    #         if rec.mm_move_id:
    #             rec.tenancy_id = rec.mm_move_id.tenancy_id.id
    #             rec.property_id = rec.mm_move_id.property_id.id
    #         else:
    #             rec.tenancy_id = False
    #             rec.property_id = False

    #     return records

 