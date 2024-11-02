# See LICENSE file for full copyright and licensing details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    property_inv_type = fields.Selection(
        [('manual', 'Manual'), ('automatic', 'Automatic'), ],
        'Invoice type', default='manual', config_parameter='property_auto_invoice.inv_type')
