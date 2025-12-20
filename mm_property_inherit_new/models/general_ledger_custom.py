from odoo import models, api, _


class AccountReport(models.Model):
    _inherit = 'account.report'

    @api.model
    def _get_column_values(self, report, options, column, aml_values, groupby_keys):
        """Override to handle custom column values"""
        if column.get('expression_label') in ['bill_reference', 'memo']:
            # Return the value directly for string columns
            return aml_values.get(column['expression_label'], '')
        
        return super()._get_column_values(report, options, column, aml_values, groupby_keys)


class GeneralLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'
    _description = 'General Ledger Custom Handler'

    @api.model
    def _get_query_amls(self, report, options, expanded_account_ids, offset=0, limit=None):
        """Override to include account.move.ref (bill reference) in the query"""
        query, params = super()._get_query_amls(report, options, expanded_account_ids, offset=offset, limit=limit)
        
        # Inject move.ref into the SELECT clause
        # The table is aliased as 'move' not 'account_move'
        if 'SELECT' in query and 'move.ref AS move_ref' not in query:
            # Add move.ref right after existing selections
            query = query.replace(
                'account_move_line.name,',
                'account_move_line.name, move.ref AS move_ref,',
                1
            )
            # Fallback: if the above doesn't work, try another pattern
            if 'move_ref' not in query:
                query = query.replace(
                    'account_move_line.ref,',
                    'account_move_line.ref, move.ref AS move_ref,',
                    1
                )
        
        return query, params

    def _get_aml_values(self, report, options, expanded_account_ids, offset=0, limit=None):
        """Override to add bill_reference to result"""
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
            
            # Set communication field
            if aml_result.get('ref'):
                aml_result['communication'] = f"{aml_result['ref']} - {aml_result['name']}"
                aml_result['memo'] = aml_result['ref']
            else:
                aml_result['communication'] = aml_result['name']
                aml_result['memo'] = ''
            
            # Set bill_reference from move.ref
            aml_result['bill_reference'] = aml_result.get('move_ref', '') or ''
            
            # The same aml can return multiple results when using account_report_cash_basis module
            aml_key = (aml_result['id'], aml_result['date'])
            account_result = rslt[aml_result['account_id']]
            
            if aml_key not in account_result:
                account_result[aml_key] = {col_group_key: {} for col_group_key in options['column_groups']}
            
            already_present_result = account_result[aml_key][aml_result['column_group_key']]
            
            if already_present_result:
                # In case the same move line gives multiple results at the same date, add them
                already_present_result['debit'] += aml_result['debit']
                already_present_result['credit'] += aml_result['credit']
                already_present_result['balance'] += aml_result['balance']
                already_present_result['amount_currency'] += aml_result['amount_currency']
                # Keep the bill_reference from the first occurrence
                if not already_present_result.get('bill_reference'):
                    already_present_result['bill_reference'] = aml_result['bill_reference']
            else:
                account_result[aml_key][aml_result['column_group_key']] = aml_result
        
        return rslt, has_more