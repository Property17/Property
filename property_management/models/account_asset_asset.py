# See LICENSE file for full copyright and licensing details

from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError  


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'
    _description = 'Asset'
    
    
    
    def action_asset_modify_new(self):
        return self.action_asset_modify()
    
    @api.depends('property_phase_ids', 'property_phase_ids.lease_price')
    def _compute_sales_rates(self):
        """
        This Method is used to calculate total sales rates.
        @param self: The object pointer
        @return: Calculated Sales Rate.
        """
        for prop_rec in self:
            counter = 0
            les_price = 0
            sal_rate = 0
            for phase in prop_rec.property_phase_ids:
                counter += 1
                les_price += phase.lease_price
            if counter != 0 and les_price != 0:
                sal_rate = les_price / counter
            prop_rec.sales_rates = sal_rate

    @api.depends('roi')
    def _compute_ten_year_roi(self):
        """
        This Method is used to Calculate ten years ROI(Return On Investment).
        @param self: The object pointer
        @return: Calculated Return On Investment.
        """
        for rec in self:
            rec.ten_year_roi = 10 * rec.roi

    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent')
    def _compute_roi(self):
        """
        This Method is used to Calculate ROI(Return On Investment).
        @param self: The object pointer
        @return: Calculated Return On Investment.
        """
        for prop_rec in self:
            prop_rec.roi = \
                sum(gain.rent for gain in prop_rec.tenancy_property_ids)

    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent',
                 'property_phase_ids')
    def _compute_operational_costs(self):
        """
        This Method is used to Calculate Operation Cost.
        @param self: The object pointer
        @return: Calculated Operational Cost.
        """
        for prop_rec in self:
            operational_cost = 0
            opr_cst = 0
            gain_from_investment = sum(gain.rent for gain in
                                       prop_rec.tenancy_property_ids)
            for phase in prop_rec.property_phase_ids:
                operational_cost += (phase.lease_price / 100)
            if gain_from_investment != 0 and operational_cost != 0:
                opr_cst = operational_cost / gain_from_investment
            prop_rec.operational_costs = opr_cst

    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.date',
                 'tenancy_property_ids.date_start')
    def _compute_occupancy_rates(self):
        """
        This Method is used to calculate occupancy rate.
        @param self: The object pointer
        @return: Calculated Occupancy Rate.
        """
        for prop_rec in self:
            diffrnc = 0
            occ_rate = 0
            if prop_rec.acquisition_date:
                pur_diff = fields.Date.context_today(self) - prop_rec.acquisition_date
                purchase_diff = pur_diff.days
                for tency_rec in prop_rec.tenancy_property_ids:
                    if tency_rec.date and tency_rec.date_start:
                        date_diff = \
                            tency_rec.date - tency_rec.date_start
                        diffrnc += date_diff.days
                if purchase_diff != 0 and diffrnc != 0:
                    occ_rate = (purchase_diff * 100) / diffrnc
                prop_rec.occupancy_rates = occ_rate

    # @api.depends('original_value','salvage_value','depreciation_move_ids')
    # def _compute_value_residual(self):
    #     """
    #     @param self: The object pointer
    #     @return: Calculated Residual Amount.
    #     """
        
    #     for rec in self:
    #         total_residual = 0.0
    #         if rec.original_value > 0:
    #             total_amount = sum(
    #                 line.amount for line in rec.depreciation_move_ids
    #                 if line.move_check)
    #             total_residual = \
    #                 rec.original_value - total_amount - rec.salvage_value
    #         rec.value_residual = total_residual

    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.rent_schedule_ids')
    def _compute_simulation(self):
        """
        This Method is used to calculate simulation
        which is used in Financial Performance Report.
        @param self: The object pointer
        @return: Calculated Simulation Amount.
        """
        for property_data in self:
            property_data.simulation = sum(
                rent_schedule.amount for tenancy_property in
                property_data.tenancy_property_ids for rent_schedule in
                tenancy_property.rent_schedule_ids)

    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.rent_schedule_ids',
                 'tenancy_property_ids.rent_schedule_ids.move_check')
    def _compute_revenue(self):
        """
        This Method is used to calculate revenue
        which is used in Financial Performance Report.
        @param self: The object pointer
        @return: Calculated Revenue Amount.
        """
        for property_data in self:
            property_data.revenue = sum(
                rent_schedule.amount for tenancy_property in
                property_data.tenancy_property_ids for rent_schedule in
                tenancy_property.rent_schedule_ids if
                rent_schedule.move_check)

    @api.depends('gfa_feet', 'unit_price')
    def _compute_total_price(self):
        """
        This Method is used to Calculate Total Price.
        @param self: The object pointer
        @return: Calculated Total Price.
        """
        for rec in self:
            rec.total_price = rec.gfa_feet * rec.unit_price

    is_property = fields.Boolean('Is Property', default=False)
    property_sale_rent = fields.Selection(string='Property For Sale/Rent',
                                          selection=[('rent', 'Property For Rent')],
                                          copy=False, default='rent')
    image = fields.Binary("Logo", attachment=True,
        help="This field holds the image used as logo for the brand, "
             "limited to 1024x1024px.")
    simulation_date = fields.Date(
        string='Simulation Date',
        help='Simulation Date.')
    city = fields.Char(
        string='City')
    street = fields.Char(
        string='Street')
    street2 = fields.Char(
        string='Street2')
    township = fields.Char(
        string='Township')
    simulation_name = fields.Char(
        string='Simulation Name')
    construction_cost = fields.Float(
        string='Construction Cost')
    zip = fields.Char(
        string='Zip',
        size=24,
        change_default=True)
    video_url = fields.Char(
        string='Video URL',
        help="//www.youtube.com/embed/mwuPTI8AT7M?rel=0")
    unit_price = fields.Float(
        string='Unit Price',
        help='Unit Price Per Sqft.')
    ground_rent = fields.Float(
        string='Ground Rent',
        help='Ground rent of Property.')
    gfa_meter = fields.Float(
        string='GFA(m)',
        help='Gross floor area in Meter.')
    sale_price = fields.Float(
        string='Sale Price',
        help='Sale price of the Property.')
    gfa_feet = fields.Float(
        string='GFA(Sqft)',
        help='Gross floor area in Square feet.')
    sales_rates = fields.Float(
        string="Sales Rate",
        compute='_compute_sales_rates',
        help='Average Sale/Lease price from property phase per Month.')
    ten_year_roi = fields.Float(
        string="10 year ROI",
        compute='_compute_ten_year_roi',
        help="10 year Return of Investment.")
    roi = fields.Float(
        string="ROI",
        compute='_compute_roi',
        store=True,
        help='ROI ( Return On Investment ) = ( Total Tenancy rent - Total \
        maintenance cost ) / Total maintenance cost.',)
    operational_costs = fields.Float(
        string="Operational Costs(%)",
        store=True,
        compute='_compute_operational_costs',
        help='Average of total operational budget and total rent.')
    occupancy_rates = fields.Float(
        string="Occupancy Rate",
        store=True,
        compute='_compute_occupancy_rates',
        help='Total Occupancy rate of Property.')
    parent_path = fields.Char(index=True)
    # value_residual = fields.Float(
    #     string='Residual Value',
    #     method=True,
    #     compute='_compute_value_residual',)
    simulation = fields.Float(
        string='Total Amount',
        compute='_compute_simulation',
        store=True)
    revenue = fields.Float(
        string='Revenue',
        compute='_compute_revenue',
        store=True)
    total_price = fields.Float(
        string='Total Price',
        compute='_compute_total_price',
        help='Total Price of Property, \nTotal Price = Unit Price * \
        GFA (Sqft).')
    pur_instl_chck = fields.Boolean(
        string='Purchase Installment Check',
        default=False)
    sale_instl_chck = fields.Boolean(
        string='Sale Installment Check',
        default=False)
    color = fields.Integer(
        string='Color',
        default=4)
    floor = fields.Integer(
        string='Floor',
        help='Number of Floors.')
    no_of_towers = fields.Integer(
        string='No of Towers',
        help='Number of Towers.')
    no_of_property = fields.Integer(
        string='Property Per Floors.',
        help='Number of Properties Per Floor.')
    income_acc_id = fields.Many2one(
        comodel_name='account.account',
        string='Income Account',
        help='Income Account of Property.')
    expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Expense Account',
        help='Expense Account of Property.')
    parent_id = fields.Many2one(
        comodel_name='account.asset',
        string='Parent Property')
    maint_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Maintenance Account')
    current_tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Current Tenant')
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        ondelete='restrict')
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Property State',
        ondelete='restrict')
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type',
        help='Types of property.',
        index=True)
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type',
        help='Type of Rent.')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact Name',
        domain="[('tenant', '=', True)]")
    property_manager = fields.Many2one(
        comodel_name='res.partner',
        string='Property Manager')
    room_ids = fields.One2many(
        comodel_name='property.room',
        inverse_name='property_id',
        string='Rooms')
    property_phase_ids = fields.One2many(
        comodel_name='property.phase',
        inverse_name='property_id',
        string='Phase')
    property_photo_ids = fields.One2many(
        comodel_name='property.photo',
        inverse_name='property_id',
        string='Photos')
    floor_plans_ids = fields.One2many(
        comodel_name='property.floor.plans',
        inverse_name='property_id',
        string='Floor Plans ')
    utility_ids = fields.One2many(
        comodel_name='property.utility',
        inverse_name='property_id',
        string='Utilities')
    nearby_ids = fields.One2many(
        comodel_name='nearby.property',
        inverse_name='property_id',
        string='Nearest Property')
    contract_attachment_ids = fields.One2many(
        comodel_name='property.attachment',
        inverse_name='property_id',
        string='Document')
    child_ids = fields.One2many(
        comodel_name='account.asset',
        inverse_name='parent_id',
        string='Children Assets')
    property_insurance_ids = fields.One2many(
        comodel_name='property.insurance',
        inverse_name='property_id',
        string='Insurance')
    tenancy_property_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='property_id',
        string='Tenancy Property')
    safety_certificate_ids = fields.One2many(
        comodel_name='property.safety.certificate',
        inverse_name='property_id',
        string='Safety Certificate')
    account_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='property_id',
        string='Entries',
        readonly=True,
        states={'draft': [('readonly', False)]})
    # TODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODO
    
    # depreciation_line_ids = fields.One2many(
    #     comodel_name='account.asset.depreciation.line',
    #     inverse_name='asset_id',
    #     string='Depreciation Lines',
    #     readonly=True,
    #     states={'draft': [('readonly', False)]})
    bedroom = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Bedrooms',
        default='1')
    bathroom = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Bathrooms',
        default='1')
    parking = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Parking',
        default='1')
    facing = fields.Selection(
        [('north', 'North'), ('south', 'South'),
         ('east', 'East'), ('west', 'West')],
        string='Facing',
        default='east')
    furnished = fields.Selection(
        [('none', 'None'),
         ('semi_furnished', 'Semi Furnished'),
         ('full_furnished', 'Full Furnished')],
        string='Furnishing',
        default='none',
        help='Furnishing.')
    state = fields.Selection(
        selection_add=[
         ('new_draft', 'Booking Open'),
         ('draft', 'Available'),
         ('book', 'Booked'),
         ('normal', 'On Lease'),
         ('close', 'Sale'),
         ('sold', 'Sold'),
         ('open', 'Running'),
         ('cancel', 'Cancel')],
        ondelete={
            'new_draft': 'set default',
            'draft': 'set default',
            'book': 'set default',
            'normal': 'set default',
            'close': 'set default',
            'sold': 'set default',
            'open': 'set default',
            'cancel': 'set default',
        },
        string='State',
        required=True,
        default='draft')
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type')
    latitude = fields.Float(
        string='Latitude',
        digits=(16, 8),
        help='Latitude of the place.')
    longitude = fields.Float(
        string='Longitude',
        digits=(16, 8),
        help='Longitude of the place.')
    note = fields.Text()
    tenancy_entries_count = fields.Integer(
        compute='_get_tenancy_count', string='Tenancy')
    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    prorata_date = fields.Date(string="Prorata Date", default=fields.Date.today())
    
    def _get_tenancy_count(self):
        self.tenancy_entries_count = len(self.tenancy_property_ids)

    def open_tenancy(self):
        context = dict(self._context) or {}
        action = self.env["ir.actions.act_window"]._for_xml_id(
            'property_management.action_property_analytic_view')
        action['domain'] = [('property_id', '=', self.id),
                            ('resident_type', '=', 'tenant_tenancy')]
        action['context'] = {'create': False, 'is_property': True,
                             'default_resident_type': 'tenant_tenancy'}
        return action


    @api.model
    def create(self, vals):
        """
        This Method is used to overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if 'message_follower_ids' in vals:
            del vals['message_follower_ids']
        # vals['code'] = self.env['ir.sequence'].next_by_code('property')
        if vals.get('parent_id'):
            parent_periods = self.browse(vals.get('parent_id'))
            if vals.get('name') == parent_periods.name:
                raise ValidationError(_('Parent Property should not be same '
                                        'as current Property !!'))
            if parent_periods.rent_type_id and parent_periods.rent_type_id.id:
                vals.update({'rent_type_id': parent_periods.rent_type_id.id})
        # acc_analytic_id = self.env['account.analytic.account'].sudo()
        # acc_analytic_id.create({'name': vals['name']})
        # image_resize_images(vals, sizes={'image': (1024, None)})
        return super(AccountAssetAsset, self).create(vals)

    def write(self, vals):
        """
        This Method is used to overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        state_color = {
            'new_draft':0, 'draft':4,
            'book': 2, 'normal': 7,
            'close': 9, 'sold': 9,
            'cancel': 1, 'open':10}
        if 'state' in vals:
            vals.update({'color': state_color[vals['state']]})
        if vals.get('parent_id'):
            parent_periods = self.browse(vals.get('parent_id'))
            if self.name == parent_periods.name:
                raise ValidationError(_('Parent Property should not be same '
                                        'as current Property !!'))
        # image_resize_images(vals, sizes={'image': (1024, None)})
        return super(AccountAssetAsset, self).write(vals)

    def create_tenancy(self):
        analytic_account_obj = self.env['account.analytic.account']
        for account_asset in self:
            account_asset_values = {
                'name': account_asset.name,
                'property_id': account_asset.id,
                'resident_type': 'tenant_tenancy',
            }
            account_asset_id = analytic_account_obj.create(account_asset_values)
            account_asset_id.onchange_date_start()
            account_asset_form_id = self.env.ref('property_management.property_analytic_view_form').id

        return {
            'view_type': 'form',
            'view_id': account_asset_form_id,
            'view_mode': 'form',
            'res_model': 'account.analytic.account',
            'res_id': account_asset_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.onchange('parent_id')
    def parent_property_onchange(self):
        """
        when you change Parent Property, this method will change
        address fields values accordingly.
        @param self: The object pointer
        """
        if self.parent_id:
            self.street = self.parent_id.street or ''
            self.street2 = self.parent_id.street2 or ''
            self.township = self.parent_id.township or ''
            self.city = self.parent_id.city or ''
            self.state_id = self.parent_id.state_id.id or False
            self.zip = self.parent_id.zip or ''
            self.country_id = self.parent_id.country_id.id or False

    @api.onchange('gfa_feet')
    def sqft_to_meter(self):
        """
        when you change GFA Feet, this method will change
        GFA Meter field value accordingly.
        @param self: The object pointer
        @return: Calculated GFA Feet.
        """
        meter_val = 0.0
        if self.gfa_feet:
            meter_val = float(self.gfa_feet / 10.7639104)
        self.gfa_meter = meter_val

    @api.onchange('unit_price', 'gfa_feet')
    def unit_price_calc(self):
        """
        when you change Unit Price and GFA Feet fields value,
        this method will change Total Price and Purchase Value
        accordingly.
        @param self: The object pointer
        """
        if self.unit_price and self.gfa_feet:
            self.total_price = float(self.unit_price * self.gfa_feet)
            self.original_value = float(self.unit_price * self.gfa_feet)
        if self.unit_price and not self.gfa_feet:
            raise ValidationError(_('Please Insert GFA(Sqft).'))

    def edit_status(self):
        """
        This method is used to change property state to book.
        @param self: The object pointer
        """
        for rec in self:
            if not rec.property_manager:
                raise ValidationError(_('Please select Property Manager!'))
        return self.write({'state': 'book'})

    def edit_status_book(self):
        """
        This method will open a wizard.
        @param self: The object pointer
        """
        context = dict(self._context)
        for rec in self:
            context.update({'edit_result': rec.id})
        return {
            'name': ('wizard'),
            'res_model': 'book.available.wiz',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }

    def open_url(self):
        """
        This Button method is used to open a URL
        according fields values.
        @param self: The object pointer
        """
        url = "http://maps.google.com/maps?oi=map&q="
        for line in self:
            if line.name:
                street_s = re.sub(r'[^\w]', ' ', line.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.street:
                street_s = re.sub(r'[^\w]', ' ', line.street)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.street2:
                street_s = re.sub(r'[^\w]', ' ', line.street2)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.township:
                street_s = re.sub(r'[^\w]', ' ', line.township)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.city:
                street_s = re.sub(r'[^\w]', ' ', line.city)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.state_id:
                street_s = re.sub(r'[^\w]', ' ', line.state_id.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.country_id:
                street_s = re.sub(r'[^\w]', ' ', line.country_id.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.latitude:
                street_s = re.sub(r'[^\w]', ' ', str(line.latitude))
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.street2:
                street_s = re.sub(r'[^\w]', ' ', str(line.longitude))
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'

            if line.zip:
                url += line.zip
        return {
                'name': _('Go to website'),
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'current',
                'url': url
            }

    def button_normal(self):
        """
        This Button method is used to change property state to On Lease.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'normal'})

    def button_sold(self):
        """
        This Button method is used to change property state to Sold.
        @param self: The object pointer
        """
        invoice_obj = self.env['account.move']
        for data in self:
            if not data.expense_account_id:
                raise UserError(_('Please Configure Income \
                                Account from Property!'))
            inv_line_values = {
                'name': data.name or "",
                'ref': 'account.asset',
                'quantity': 1,
                'account_id': data.income_acc_id.id or False,
                'price_unit': data.sale_price or 0.00,
            }

            inv_values = {
                'ref': data.name or "",
                'move_type': 'out_invoice',
                'property_id': data.id,
                'partner_id': data.customer_id.id or False,
                'payment_id': data.payment_term.id,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'date': fields.Date.context_today(self) or False,
                # 'number': data.code or '',
            }
            invoice_obj.create(inv_values)
            data.write({'state': 'sold'})
        return True

    def button_close(self):
        """
        This Button method is used to change property state to Sale.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'close'})

    def button_cancel(self):
        """
        This Button method is used to change property state to Cancel.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'cancel'})

    def button_draft(self):
        """
        This Button method is used to change property state to Available.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'draft'})

    def date_addition(self, starting_date, end_date, period):
        date_list = []
        if period == 'monthly':
            while starting_date < end_date:
                date_list.append(starting_date)
                res = ((
                    starting_date + relativedelta(months=1)))
                starting_date = res
            return date_list
        else:
            while starting_date < end_date:
                date_list.append(starting_date)
                res = ((
                    starting_date + relativedelta(years=1)))
                starting_date = res
            return date_list
    # TODO
    # def unlink(self):
    #     for rec in self:
    #         property_id = self.env['commission.invoice'].search([
    #             ('property_id', '=', rec.id), ('state','=','invoice')])
    #         if property_id:
    #             raise ValidationError(_('Property should not be delete '
    #                                     'because of Commision invoice '
    #                                     'generated !!'))
    #         if rec.state not in ['draft', 'cancel']:
    #             raise ValidationError(_('You cannot delete property which contract is in Progress or Booked.'))
    #     return super(AccountAssetAsset, self).unlink()
