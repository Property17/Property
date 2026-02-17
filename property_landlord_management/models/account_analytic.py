# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.depends('deposit')
    def _compute_payment_type(self):
        """
        This method is used to set deposit return and deposit received
        boolean field accordingly to current Tenancy.
        @param self: The object pointer
        """
        res = super(AccountAnalyticAccount, self)._compute_payment_type()
        if self._context.get('is_landlord_rent'):
            for tennancy in self:
                for payment in self.env['account.payment'].search(
                        [('tenancy_id', '=', tennancy.id),
                         ('state', '=', 'posted')]):
                    if payment.payment_type == 'outbound':
                        tennancy.deposit_received = True
                    if payment.payment_type == 'inbound':
                        tennancy.deposit_return = True
        return res

    property_owner_id = fields.Many2one(
        string='Owner',
        comodel_name='landlord.partner',
        help="Owner of property.")
    landlord_rent = fields.Monetary(string='Landlord Rent',currency_field='currency_id')
    resident_type = fields.Selection(selection_add=[('landlord_partner', 'Landlord Partner')])

    @api.onchange('property_id')
    def _onchange_property(self):
        if self.property_id:
            self.property_owner_id = self.property_id.property_owner.id

    def create_rent_schedule_landlord(self):
        """
        This button method is used to create rent schedule Lines.
        @param self: The object pointer
        """
        rent_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            amount = tenancy_rec.landlord_rent
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
                    for wek_rec in range(wek_tot1):
                        rent_obj.create(
                            {
                                'start_date': d1,
                                'amount': amount * interval or 0.0,
                                'property_id': tenancy_rec.property_id and
                                tenancy_rec.property_id.id or False,
                                'tenancy_id': tenancy_rec.id,
                                'currency_id': tenancy_rec.currency_id.id or
                                False,
                                'rel_tenant_id': tenancy_rec.tenant_id.id
                            })
                        d1 = d1 + relativedelta(days=(7 * interval))
                if wek_tot > 0:
                    one_day_rent = 0.0
                    if amount:
                        one_day_rent = (amount) / (7 * interval)
                    rent_obj.create({
                        'start_date': d1.strftime(
                            DEFAULT_SERVER_DATE_FORMAT),
                        'amount': (one_day_rent * (wek_tot)) or 0.0,
                        'property_id': tenancy_rec.property_id and
                        tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id
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
                    tot_rec = int(tot_rec)
                    for rec in range(tot_rec):
                        rent_obj.create({
                            'start_date': d1.strftime(
                                DEFAULT_SERVER_DATE_FORMAT),
                            'amount': amount * interval or 0.0,
                            'property_id': tenancy_rec.property_id and
                            tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or
                            False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id
                        })
                        d1 = d1 + relativedelta(months=interval)
                if tot_rec2 > 0:
                    rent_obj.create({
                        'start_date': d1.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'amount': amount * tot_rec2 or 0.0,
                        'property_id': tenancy_rec.property_id and
                        tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id
                    })
        return self.write({'rent_entry_chck': True})

    @api.model
    def create(self, vals):
        """
        This Method is used to overrides orm create method,
        to change state and tenant of related property.
        ---------------------------------------------------
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        res = super(AccountAnalyticAccount, self).create(vals)
        if self._context.get('is_landlord_rent'):
            res.code = self.env['ir.sequence'].next_by_code(
                'landlord.rent')
            if 'property_id' in vals:
                prop_brw = self.env['account.asset'].browse(
                    vals['property_id'])
                if not prop_brw.property_owner:
                    prop_brw.write(
                        {'property_owner': vals.get('property_owner_id')})
        return res

    def unlink(self):
        """
        Overrides orm unlink method,
        @param self: The object pointer
        @return: True/False.
        """
        if self._context.get('is_landlord_rent'):
            rent_ids = []
            for tenancy_rec in self:
                analytic_ids = self.env['account.analytic.line'].search(
                    [('account_id', '=', tenancy_rec.id)])
                if analytic_ids and analytic_ids.ids:
                    analytic_ids.unlink()
                rent_ids = self.env['tenancy.rent.schedule'].search(
                    [('tenancy_id', '=', tenancy_rec.id)])
                post_rent = [x.id for x in rent_ids if x.move_check is True]
                if post_rent:
                    raise ValidationError(
                        _('''You cannot delete Tenancy record, 
                        if any related Rent Schedule entries are in posted.'''))
                else:
                    rent_ids.unlink()
        return super(AccountAnalyticAccount, self).unlink()

    def landlord_button_start(self):
        """
        This button method is used to Change Tenancy state to Open.
        -----------------------------------------------------------
        @param self: The object pointer
        """
        if self._context.get('is_landlord_rent'):
            self.write({'state': 'open', 'rent_entry_chck': False})

    def landlord_button_deposite_pay(self):
        """
        This button method is used to open the related
        account payment form view.
        @param self: The object pointer
        @return: Dictionary of values.
        """
        context = dict(self._context) or {}
        payment_id = False
        acc_pay_form = self.env.ref(
            'account.view_account_payment_form')
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        payment_obj = self.env['account.payment']
        payment_method_id = self.env.ref(
            'account.account_payment_method_manual_out')
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
                'partner_id': tenancy_rec.property_owner_id.parent_id.id,
                'partner_type': 'supplier',
                'journal_id': account_jrnl_obj.id,
                'payment_type': 'outbound',
                'ref': 'Deposit Received',
                'tenancy_id': tenancy_rec.id,
                'amount': tenancy_rec.deposit,
                'property_id': tenancy_rec.property_id.id,
                'payment_method_id': payment_method_id.id
            }
            payment_id = payment_obj.create(vals)
        return {
                'view_mode': 'form',
                'view_id': acc_pay_form.id,
                'view_type': 'form',
                'res_id': payment_id and payment_id.id,
                'res_model': 'account.payment',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'domain': '[]',
                'context': context
            }

    def landlord_button_deposite_received(self):
        """
        This button method is used to open the related
        account payment form view.
        @param self: The object pointer
        @return: Dictionary of values.
        """
        payment_id = False
        acc_pay_form = self.env.ref(
            'account.view_account_payment_form')
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        payment_method_id = self.env.ref(
            'account.account_payment_method_manual_in')
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
                    'context': self._context,
                }
            if tenancy_rec.deposit == 0.00:
                raise ValidationError(_('Please Enter Deposit amount.'))
            if tenancy_rec.deposit < 0.00:
                raise ValidationError(
                    _('The deposit amount must be strictly positive.'))
            vals = {
                'partner_id': tenancy_rec.property_owner_id.parent_id.id,
                'partner_type': 'customer',
                'journal_id': account_jrnl_obj.id,
                'payment_type': 'inbound',
                'ref': 'Deposit Received',
                'tenancy_id': tenancy_rec.id,
                'amount': tenancy_rec.deposit,
                'property_id': tenancy_rec.property_id.id,
                'payment_method_id': payment_method_id.id
            }
            payment_id = self.env['account.payment'].create(vals)
        return {
                'view_mode': 'form',
                'view_id': acc_pay_form.id,
                'view_type': 'form',
                'res_id': payment_id and payment_id.id,
                'res_model': 'account.payment',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': '[]',
                'context': {
                    'close_after_process': True,
                }
            }

    def landlord_button_close(self):
        """
        This button method is used to Change Tenancy state to close.
        @param self: The object pointer
        """
        return self.write({'state': 'close'})

    def landlord_button_cancel_tenancy(self):
        """
        This button method is used to Change Tenancy state to Cancelled.
        @param self: The object pointer
        """
        for record in self:
            self.write(
                {'state': 'cancelled', 'tenancy_cancelled': True})
            rent_ids = self.env['tenancy.rent.schedule'].search(
                [('tenancy_id', '=', record.id),
                 ('paid', '=', False),
                 ('move_check', '=', False)])
            for value in rent_ids:
                value.write({'is_readonly': True})
        return True


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"

    def create_landlord_invoice(self):
        """
        Create invoice for Rent Schedule.
        ------------------------------------
        @param self: The object pointer
        """
        if self.tenancy_id.resident_type == 'landlord_partner':
            account_jrnl_obj = self.env['account.journal'].search(
                [('type', '=', 'purchase')], limit=1)
            property_id = self.tenancy_id.property_id
            inv_lines_values = {
                # 'origin': 'tenancy.rent.schedule',
                'name': 'Rent Cost for' + self.tenancy_id.name,
                'quantity': 1,
                'price_unit': self.amount or 0.00,
                'account_id':
                    property_id.account_depreciation_expense_id.id or False,
                'analytic_account_id': self.tenancy_id.id or False,
            }
            owner_rec = self.tenancy_id.property_owner_id
            invo_values = {
                'partner_id': self.tenancy_id.property_owner_id.parent_id.id or False,
                'move_type': 'in_invoice',
                'invoice_line_ids': [(0, 0, inv_lines_values)],
                'property_id': property_id and property_id.id or False,
                'invoice_date': self.start_date or False,
                # 'account_id': owner_rec.property_account_payable_id.id,
                # 'schedule_id': self.id,
                'new_tenancy_id': self.tenancy_id.id,
                'journal_id': account_jrnl_obj.id or False
            }
            acc_id = self.env['account.move'].with_context(
                {'default_move_type': 'in_invoice'}).create(invo_values)
            self.write({'invoice_id': acc_id.id, 'is_invoiced': True})
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

    def open_landlord_invoice(self):
        """
        Description:
            This method is used to open Invoice which is created.

        Decorators:
            api.multi
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
