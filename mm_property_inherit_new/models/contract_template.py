from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ContractTemplateNew(models.Model):
    _name = "contract.template"
    _description = "Contract Template"

    name = fields.Char(string='Name')
    tenancy_id = fields.Many2one('account.analytic.account', 'Tenancy')
    temp = fields.Html(string='Temp')
