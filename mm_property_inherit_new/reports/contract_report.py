# -*- coding: utf-8 -*-
import json
from num2words import num2words
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import date, datetime, time


class ContractReportViewNew(models.AbstractModel):
    _name = "report.mm_property_inherit_new.mm_contract_report_new"
    _description = "Contract Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []

        contract_temp = self.env['property.contract.template'].search([('id', '=', docids)])

        return {
            'temp': contract_temp.temp if contract_temp.temp else " ",

        }
