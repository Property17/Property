# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    property_deposit_receivable_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Deposit Receivable Account',
        config_parameter='property_management.deposit_receivable_account_id',
        check_company=False,
        domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False)]",
        help='Single debit account for all companies on deposit receive invoices (e.g. Deposit Receivable / ذمم التأمينات).',
    )

    @api.model
    def _get_deposit_receivable_account(self):
        """Read global deposit receivable account (same account for every company)."""
        param = self.env['ir.config_parameter'].sudo().get_param(
            'property_management.deposit_receivable_account_id'
        )
        if not param:
            return self.env['account.account']
        try:
            account_id = int(param)
        except (TypeError, ValueError):
            return self.env['account.account']
        return self.env['account.account'].sudo().browse(account_id).exists()
