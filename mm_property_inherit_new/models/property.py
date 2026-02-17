from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

# test


class ActivityTypeNew(models.Model):
    _name = "activity.type"
    _description = "Activity Type"

    name = fields.Char(
        string='Name',
        size=50,
        required=True)


class LegalTypeNew(models.Model):
    _name = "legal.type"
    _description = "Legal Type"

    name = fields.Char(
        string='Name',
        size=50,
        required=True)
