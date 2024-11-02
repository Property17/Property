# See LICENSE file for full copyright and licensing detailss
from odoo.tests import common
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PropertyManagementSPTestCase(common.TransactionCase):

    def setup(self):
        super(PropertyManagementSPTestCase, self).setup()

    def test_property_action(self):
        # Property Created
        self.property_type = self.browse_ref(
            'property_management.property_type1')
        self.partner = self.browse_ref('base.res_partner_2')
        self.property_demo = self.browse_ref("property_management.property1")
        self.rent_type = self.browse_ref("property_management.rent_type1")
        self.payment_term = self.browse_ref(
            'account.account_payment_term_15days')
        self.asset = self.env['account.asset'].sudo().create(
            {
                'name': 'Radhika Recidency',
                'type_id': self.property_type,
                'state': self.property_demo.state,
                'street': self.property_demo.street,
                'city': self.property_demo.city,
                'country_id': self.property_demo.country_id.id,
                'state_id': self.property_demo.state_id.id,
                'zip': self.property_demo.zip,
                'age_of_property': self.property_demo.age_of_property,
                'category_id': self.property_demo.category_id.id,
                'value': self.property_demo.value,
                'value_residual': self.property_demo.value_residual,
                'ground_rent': self.property_demo.ground_rent,
                'sale_price': self.property_demo.sale_price,
                'furnished': self.property_demo.furnished,
                'facing': self.property_demo.facing,
                'type_id': self.property_demo.type_id.id,
                'floor': self.property_demo.floor,
                'bedroom': self.property_demo.bedroom,
                'bathroom': self.property_demo.bathroom,
                'gfa_meter': self.property_demo.gfa_meter,
                'gfa_feet': self.property_demo.gfa_feet,
                'parent_id': self.property_demo.parent_id,
                'property_manager': self.property_demo.property_manager.id,
                'income_acc_id': self.property_demo.income_acc_id.id,
                'expense_account_id': self.property_demo.expense_account_id.id,
                'rent_type_id': self.rent_type.id,
                'sale_date': '07/07/2017',
                'sale_price': 2200000.00,
                'payment_term': self.payment_term.id,
                'customer_id': self.partner.id,
                'partner_id': self.partner.id,
                'date': '07/17/2017',
                'end_date': '07/17/2018',
                'purchase_price': 3200000.00,
                'recurring_rule_type': 'monthly',
            })
        self.asset.genrate_payment_enteries()
        self.asset.create_purchase_installment()
