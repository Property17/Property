# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountAsset(models.Model):
    _inherit = 'account.asset'
    _description = 'Property'

    sale_date = fields.Date(
        string='Sale Date',
        help='Sale Date of the Property.')
    sale_price = fields.Monetary(
        string='Sale Price',
        currency_field='currency_id',
        help='Sale price of the Property.')
    payment_term = fields.Many2one(
        comodel_name='account.payment.term',
        string='Payment Terms')
    sale_cost_ids = fields.One2many(
        comodel_name='sale.cost',
        inverse_name='property_id',
        string='Costs')
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer')
    end_date = fields.Date(
        string='End Date')
    purchase_price = fields.Monetary(
        currency_field='currency_id',
        help='Purchase price of the Property.')
    multiple_owners = fields.Boolean(
        string='Multiple Owners',
        help="Check this box if there is multiple \
            Owner of the Property.")
    total_owners = fields.Integer(
        string='Number of Owners')
    recurring_rule_type = fields.Selection(
        [('monthly', 'Month(s)')],
        string='Recurrency',
        default='monthly',
        help="Invoice automatically repeat \
            at specified interval.")
    purchase_cost_ids = fields.One2many(
        comodel_name='cost.cost',
        inverse_name='property_id',
        string='Purchase Costs')
    note = fields.Text(
        string='Notes',
        help='Additional Notes.')
    return_period = fields.Float(
        compute='_compute_calc_return_period',
        string="Return Period(In Months)",
        store=True,
        help='Average of Purchase Price and Ground Rent.')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner', readonly=False)
    property_sale_rent = fields.Selection(selection_add=[('sale', 'Property For Sale')])

    @api.constrains('sale_price', 'no_of_property', 'ground_rent', 'gfa_feet', 'gfa_meter', 'unit_price')
    def check_negative_value(self):
        for property in self:
            if property.sale_price < 0:
                raise ValidationError(
                    _('You can not enter negative Sale Price.'))

    @api.constrains('property_sale_rent')
    def _constraint_property_sale_rent(self):
        for property_sale in self:
            if property_sale.state == 'normal' and property_sale.property_sale_rent == 'sale':
                raise UserError(_('You cannot change property in On Lease state!'))

    @api.model
    def create(self, values):
        res = super(AccountAsset, self).create(values)
        self._create_product_for_property_sale()
        return res

    def write(self, vals):
        res = super(AccountAsset, self).write(vals)
        for property_sale in self:
            property_sale._create_product_for_property_sale()
            move = self.env['account.move'].search(
                [('property_id', '=', property_sale.id), ('state', '=', 'draft')])
            order_line = self.env['sale.order.line'].search(
                [('product_id.product_tmpl_id.property_id', '=', property_sale.id)])
            if vals.get('property_sale_rent') and property_sale.state not in ['draft', 'close']:
                raise UserError(
                    _('Selected property already tenancy created, first cancel tenancy or you can close the contract!'))
            elif order_line and vals.get('property_sale_rent') == 'rent':
                raise UserError(
                    _('You cannot change property, Sale order found!'))
            elif move and vals.get('property_sale_rent') == 'rent':
                raise UserError(
                    _('You cannot change property, Invoice already genrated!'))
            if vals.get('property_sale_rent') and vals.get('property_sale_rent') == 'sale':
                self.button_close()
            if vals.get('property_sale_rent') and vals.get('property_sale_rent') == 'rent':
                self.button_draft()
        return res

    def _create_product_for_property_sale(self):
        for property_sale in self:
            product_tmpl = self.env['product.template'].with_context(active_test=False).search([('property_id', '=',property_sale.id)])
            if property_sale.property_sale_rent == 'sale' and not product_tmpl:
                product_tmpl = self.env['product.template'].create({
                    'name': property_sale.name,
                    'detailed_type': 'consu',
                    'list_price': property_sale.sale_price,
                    'standard_price': property_sale.value,
                    'sale_ok': True,
                    'property_id': property_sale.id,
                })
            elif product_tmpl and property_sale.property_sale_rent == 'rent':
                product_tmpl.action_archive()
            else:
                product_tmpl.action_unarchive()

    @api.constrains('sale_price')
    def check_negative_value(self):
        for property in self:
            if property.sale_price < 0:
                raise ValidationError(
                    _('You can not enter negative Sale Price.'))

    @api.depends('purchase_price', 'ground_rent')
    def _compute_calc_return_period(self):
        """
        This Method is used to Calculate Return Period.
        ------------------------------------------------
        @param self: The object pointer
        @return: Calculated Return Period.
        """
        return_period = 0
        for property_id in self:
            if property_id.ground_rent != 0 and property_id.purchase_price != 0:
                return_period = \
                    property_id.purchase_price / property_id.ground_rent
            property_id.return_period = return_period

    def create_purchase_installment(self):
        """
        This Button method is used to create purchase installment
        information entries.
        ---------------------------------------------------------
        @param self: The object pointer
        """
        year_create = []
        for res in self:
            amount = res['purchase_price']
            if amount == 0.0:
                raise UserError(_('Please Enter Valid Purchase Price'))
            if not res.end_date:
                raise UserError(_('Please Select End Date'))
            if res.end_date < res.date:
                raise UserError(
                    _("Please Select End Date greater than purchase date"))
    #        method used to calculate difference in month between two dates
            def diff_month(d1, d2):
                return (d1.year - d2.year) * 12 + d1.month - d2.month
            difference_month = diff_month(res.end_date, res.date)
            if difference_month == 0:
                amnt = amount
            else:
                if res.end_date.day > res.date.day:
                    difference_month += 1
                amnt = amount / difference_month
            # cr = self._cr
            self.env.cr.execute(
                "SELECT date FROM cost_cost WHERE property_id=%s" % res.id)
            exist_dates = self.env.cr.fetchall()
            date_add = self.date_addition(
                res.date, res.end_date, res.recurring_rule_type)
            exist_dates = map(lambda x: x[0], exist_dates)
            result = list(set(date_add) - set(exist_dates))
            result.sort(key=lambda item: item, reverse=False)
            ramnt = amnt
            remain_amnt = 0.0
            for dates in result:
                remain_amnt = amount - ramnt
                remain_amnt_per = (remain_amnt / amount) * 100
                if remain_amnt < 0:
                    remain_amnt = remain_amnt * -1
                if remain_amnt_per < 0:
                    remain_amnt_per = remain_amnt_per * -1
                year_create.append((0, 0, {
                    'currency_id': res.currency_id.id or False,
                    'date': dates,
                    'property_id': res.id,
                    'amount': amnt,
                    'remaining_amount': remain_amnt,
                    'rmn_amnt_per': remain_amnt_per,
                }))
                amount = remain_amnt
        return self.write({
            'purchase_cost_ids': year_create,
            'pur_instl_chck': True
        })

    def genrate_payment_enteries(self):
        """
        This Button method is used to generate property sale payment entries.
        ----------------------------------------------------------------------
        @param self: The object pointer
        """
        for data in self:
            amount = data.sale_price
            year_create = []
            if not data.payment_term:
                raise UserError(_('Please add Payment Terms !!'))
            pterm_list = data.payment_term.compute(
                data.sale_price, data.sale_date)
            if amount == 0.0:
                raise UserError(_('Please Enter Valid Sale Price'))
            rmnt = 0.0
            for line in pterm_list:
                lst = line[1]
                remain_amnt = amount - lst
                remain_amnt_per = (remain_amnt / data.sale_price) * 100
                if remain_amnt < 0:
                    remain_amnt = remain_amnt * -1
                if remain_amnt_per < 0:
                    remain_amnt_per = remain_amnt_per * -1
                year_create.append((0, 0, {
                    'currency_id': data.currency_id.id or False,
                    'date': line[0],
                    'property_id': data.id,
                    'amount': lst,
                    'remaining_amount': remain_amnt,''
                    'rmn_amnt_per': remain_amnt_per,
                }))
                amount = amount - lst
            self.write({
                'sale_cost_ids': year_create,
                'sale_instl_chck': True
            })
        return True

    def button_sold(self):
        """
        This Button method is used to change property state to Sold.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'sold'})

    def button_close(self):
        """
        This Button method is used to change property state to Sale.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'close'})
