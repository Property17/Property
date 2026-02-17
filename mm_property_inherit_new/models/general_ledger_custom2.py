
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json

from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from odoo.tools import get_lang
from odoo.exceptions import UserError

from datetime import timedelta
from collections import defaultdict

class GeneralLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'
    _description = 'General Ledger Custom Handler'
    
    def _get_aml_values(self, report, options, expanded_account_ids, offset=0, limit=None):
        rslt = {account_id: {} for account_id in expanded_account_ids}
        aml_query, aml_params = self._get_query_amls(report, options, expanded_account_ids, offset=offset, limit=limit)
        self._cr.execute(aml_query, aml_params)
        aml_results_number = 0
        has_more = False
        for aml_result in self._cr.dictfetchall():
            aml_results_number += 1
            if aml_results_number == limit:
                has_more = True
                break

            # if aml_result['ref']:
            #     aml_result['communication'] = f"{aml_result['ref']} - {aml_result['name']}"
            # else:
            #     aml_result['communication'] = aml_result['name']
            
            if aml_result['ref']:
                aml_result['communication'] = aml_result['ref']
                aml_result['memo'] = aml_result['ref']
            else:
                aml_result['communication'] = aml_result['name']
                aml_result['memo'] = aml_result['ref']

            # The same aml can return multiple results when using account_report_cash_basis module, if the receivable/payable
            # is reconciled with multiple payments. In this case, the date shown for the move lines actually corresponds to the
            # reconciliation date. In order to keep distinct lines in this case, we include date in the grouping key.
            aml_key = (aml_result['id'], aml_result['date'])

            account_result = rslt[aml_result['account_id']]
            if not aml_key in account_result:
                account_result[aml_key] = {col_group_key: {} for col_group_key in options['column_groups']}

            already_present_result = account_result[aml_key][aml_result['column_group_key']]
            if already_present_result:
                # In case the same move line gives multiple results at the same date, add them.
                # This does not happen in standard GL report, but could because of custom shadowing of account.move.line,
                # such as the one done in account_report_cash_basis (if the payable/receivable line is reconciled twice at the same date).
                already_present_result['debit'] += aml_result['debit']
                already_present_result['credit'] += aml_result['credit']
                already_present_result['balance'] += aml_result['balance']
                already_present_result['amount_currency'] += aml_result['amount_currency']
            else:
                account_result[aml_key][aml_result['column_group_key']] = aml_result

        return rslt, has_more


# class GeneralLedgerCustomHandler(models.AbstractModel):
#     _inherit = 'account.general.ledger.report.handler'
#     _description = 'General Ledger Custom Handler'
    
#     def _get_aml_values(self, report, options, expanded_account_ids, offset=0, limit=None):
#         rslt = {account_id: {} for account_id in expanded_account_ids}
#         aml_query, aml_params = self._get_query_amls(report, options, expanded_account_ids, offset=offset, limit=limit)
#         self._cr.execute(aml_query, aml_params)
#         aml_results_number = 0
#         has_more = False
        
#         # Fetch all results ONCE
#         aml_results = self._cr.dictfetchall()
        
#         # Get move refs in batch
#         move_ids = [aml['move_id'] for aml in aml_results if 'move_id' in aml]
#         moves = self.env['account.move'].browse(move_ids)
#         move_ref_map = {move.id: move.ref for move in moves}
#         print("***********************************moves", moves)
#         print("***********************************move_ref_map", move_ref_map)

#         # Now iterate over the already-fetched results
#         for aml_result in aml_results:
#             aml_results_number += 1
#             if aml_results_number == limit:
#                 has_more = True
#                 break
            
#             # Get move ref from the map
#             move_ref = move_ref_map.get(aml_result.get('move_id'))
            
#             if move_ref:
#                 aml_result['move_ref'] = move_ref
            
#             # Use move_ref instead of ref for communication
#             if aml_result.get('ref'):
#                 aml_result['communication'] = f"{aml_result['ref']} - {aml_result['name']}"
#                 aml_result['memo'] = aml_result['ref']
#             else:
#                 aml_result['communication'] = aml_result['name']
#                 aml_result['memo'] = aml_result.get('ref')

#             # The same aml can return multiple results when using account_report_cash_basis module, if the receivable/payable
#             # is reconciled with multiple payments. In this case, the date shown for the move lines actually corresponds to the
#             # reconciliation date. In order to keep distinct lines in this case, we include date in the grouping key.
#             aml_key = (aml_result['id'], aml_result['date'])

#             account_result = rslt[aml_result['account_id']]
#             if not aml_key in account_result:
#                 account_result[aml_key] = {col_group_key: {} for col_group_key in options['column_groups']}

#             already_present_result = account_result[aml_key][aml_result['column_group_key']]
#             if already_present_result:
#                 # In case the same move line gives multiple results at the same date, add them.
#                 # This does not happen in standard GL report, but could because of custom shadowing of account.move.line,
#                 # such as the one done in account_report_cash_basis (if the payable/receivable line is reconciled twice at the same date).
#                 already_present_result['debit'] += aml_result['debit']
#                 already_present_result['credit'] += aml_result['credit']
#                 already_present_result['balance'] += aml_result['balance']
#                 already_present_result['amount_currency'] += aml_result['amount_currency']
#             else:
#                 account_result[aml_key][aml_result['column_group_key']] = aml_result

#         return rslt, has_more