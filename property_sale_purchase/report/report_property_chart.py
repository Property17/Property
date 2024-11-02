# See LICENSE file for full copyright and licensing details

from odoo import fields, models, tools


class PropertyFinanceReports(models.Model):
    _name = "property.finance.report"
    _description = 'Property Finance Report'
    _auto = False

    type_id = fields.Many2one('property.type', 'Property Type')
    date = fields.Date('Purchase Date')
    parent_id = fields.Many2one('account.asset', 'Parent Property')
    name = fields.Char("Property")
    purchase_price = fields.Float('Purchase Price')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'property_finance_report')
        self._cr.execute(
            """CREATE or REPLACE VIEW property_finance_report AS
            SELECT id,name,type_id,purchase_price,date 
            FROM account_asset_asset """)
