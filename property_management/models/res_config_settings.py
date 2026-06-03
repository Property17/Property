# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    property_deposit_receivable_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Deposit Receivable Account',
        domain="[('company_id', '=', company_id), ('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]",
        help='Debit account on deposit receive customer invoices (e.g. Deposit Receivable / ذمم التأمينات).',
    )

    def _deposit_receivable_config_key(self, company):
        return 'property_management.deposit_receivable_account_id_%s' % company.id

    @api.model
    def _get_deposit_receivable_account_for_company(self, company):
        """Read deposit receivable account from settings (ir.config_parameter), per company."""
        if not company:
            return self.env['account.account']
        param = self.env['ir.config_parameter'].sudo().get_param(
            self._deposit_receivable_config_key(company)
        )
        if not param:
            return self.env['account.account']
        try:
            account_id = int(param)
        except (TypeError, ValueError):
            return self.env['account.account']
        return self.env['account.account'].browse(account_id).exists()

    @api.model
    def get_values(self):
        res = super().get_values()
        company = self.env.company
        account = self._get_deposit_receivable_account_for_company(company)
        res['property_deposit_receivable_account_id'] = account.id or False
        return res

    def set_values(self):
        super().set_values()
        company = self.company_id or self.env.company
        self.env['ir.config_parameter'].sudo().set_param(
            self._deposit_receivable_config_key(company),
            self.property_deposit_receivable_account_id.id or False,
        )
