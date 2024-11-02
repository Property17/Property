# See LICENSE file for full copyright and licensing details
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleCost(models.Model):
    _name = "sale.cost"
    _description = 'Sale Cost'
    _order = 'date'

    @api.depends('move_id')
    def _compute_move_check(self):
        for sale_cost in self:
            sale_cost.move_check = bool(sale_cost.move_id)

    date = fields.Date(
        string='Date')
    name = fields.Char(
        string='Description',
        size=100)
    payment_details = fields.Char(
        string='Payment Details',
        size=100)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Purchase Entry')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    remaining_amount = fields.Monetary(
        currency_field='currency_id',
        string='Remaining Amount',
        help='Shows remaining amount in currency')
    move_check = fields.Boolean(
        string='Posted',
        compute='_compute_move_check',
        store=True)
    rmn_amnt_per = fields.Monetary(
        currency_field='currency_id',
        string='Remaining Amount In %',
        help='Shows remaining amount in Percentage')
    amount = fields.Monetary(
        currency_field='currency_id',
        string='Amount')
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')

    @api.constrains('remaining_amount', 'amount', 'rmn_amnt_per')
    def check_negative_value(self):
        for property in self:
            if property.remaining_amount < 0:
                raise ValidationError(
                    _('You can not enter negative Remaining Amount.'))
            if property.amount < 0:
                raise ValidationError(
                    _('You can not enter negative Amount.'))
            if property.rmn_amnt_per < 0:
                raise ValidationError(
                    _('You can not enter negative Remaining Amount.'))

    def create_invoice(self):
        """
        This button Method is used to create account invoice.
        @param self: The object pointer
        """
        if not self.property_id.customer_id:
            raise UserError(_('Please Select Customer!'))
        if not self.property_id.income_acc_id:
            raise UserError(_('Please Configure Income Account from Property!'))
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)

        inv_line_values = {
            # 'origin': 'sale.cost',
            'name': _('Purchase Cost For ') + self.property_id.name,
            'price_unit': self.amount or 0.00,
            'quantity': 1,
            'account_id': self.property_id.income_acc_id.id,
        }

        inv_values = {
            'invoice_payment_term_id': self.property_id.payment_term.id
                                       or False,
            'partner_id': self.property_id.customer_id.id or False,
            'move_type': 'out_invoice',
            'property_id': self.property_id.id or False,
            'invoice_line_ids': [(0, 0, inv_line_values)],
            'journal_id': account_jrnl_obj and account_jrnl_obj.id or False,
        }
        acc_id = self.env['account.move'].with_context(
            {'default_type': 'out_invoice'}).create(inv_values)
        self.write({'invoice_id': acc_id.id, 'move_check': True})
        context = dict(self._context or {})
        wiz_form_id = self.env.ref('account.view_move_form').id
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }

    def open_invoice(self):
        """
        This Method is used to Open invoice
        @param self: The object pointer
        """
        context = dict(self._context or {})
        wiz_form_id = self.env.ref('account.view_move_form').id
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }
