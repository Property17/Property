# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import json
import io
from odoo.tools import date_utils
import base64
import math

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class CommonXlsxOut(models.TransientModel):
    _name = 'common.xlsx.out'

    filedata = fields.Binary('Download file', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)

class PropertyContractsReportWiz(models.TransientModel):
    
    _name = 'property.contracts.report.wiz'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    company_id = fields.Many2one('res.company', string='Company')
    property_manager_id = fields.Many2one('res.partner', domain="[('is_manager', '=', True), ('company_id', '=', company_id)]", string='Property Manager')
    parent_property_id = fields.Many2one('account.asset', domain="[('parent_id', '=', False), ('property_manager', '=', property_manager_id)]", string='Parent Property')


    def print_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'from_date': self.from_date,
                'to_date': self.to_date,
                'company_id': self.company_id.name if self.company_id else '',
                'property_manager_id': self.property_manager_id.name if self.property_manager_id else '',
                'parent_property_id': self.parent_property_id.name if self.parent_property_id else '',
            },
        }
        return self.env.ref('mm_property_inherit_new.property_contracts_report_id').report_action(self, data=data)
    
    def generate_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Property with Contracts')
        sheet.set_zoom(90)

        # Formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 13,
            'align': 'center',
            'valign': 'vcenter',
        })
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        label_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'left'
        })
        date_format = workbook.add_format({'num_format': 'm/d/yyyy', 'align': 'left'})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        normal_format = workbook.add_format({'align': 'left', 'border': 1})
        money_cell_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'border': 1})
        center_border = workbook.add_format({'align': 'center', 'border': 1})
        parent_title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'valign': 'vcenter'
        })
        note_format = workbook.add_format({
            'bg_color': '#FFFF00',
            'border': 1,
            'align': 'left',
            'valign': 'top'
        })

        # Column widths
        column_widths = [6, 40, 15, 20, 25, 25, 15, 15, 20, 15, 15, 15, 15, 15]
        for i, width in enumerate(column_widths):
            sheet.set_column(i, i, width)

        # Get report data
        data = {
            'form': {
                'from_date': str(self.from_date) if self.from_date else '',
                'to_date': str(self.to_date) if self.to_date else '',
                'company_id': self.company_id.name if self.company_id else '',
                'property_manager_id': self.property_manager_id.name if self.property_manager_id else '',
                'parent_property_id': self.parent_property_id.name if self.parent_property_id else '',
            },
            'ids': self.ids,
            'model': self._name,
        }

        report_data = self.env['report.mm_property_inherit_new.tem_property_contracts_report_id']._get_report_values(self.ids, data)
        grouped_data = report_data.get('grouped_data', {})

        # Header Section
        row = 0
        sheet.write(row, 2, 'Print Date :', label_format)
        print_date = datetime.now().strftime('%m/%d/%Y')
        sheet.write(row, 3, print_date, date_format)
        row += 1
        
        if self.from_date or self.to_date:
            from_date_str = self.from_date.strftime('%m/%d/%Y') if self.from_date else ''
            to_date_str = self.to_date.strftime('%m/%d/%Y') if self.to_date else ''
            sheet.write(row, 3, from_date_str, date_format)
            sheet.write(row, 4, 'TO', label_format)
            sheet.write(row, 5, to_date_str, date_format)
            row += 1

        # Process each parent property group
        for parent_prop_name, group_info in grouped_data.items():
            company_name = group_info.get('company_name', '')
            property_manager = group_info.get('property_manager', '')
            properties = group_info.get('properties', [])
            
            row += 1  # Spacing before group
            
            # Company Info
            sheet.write(row, 1, 'Company', label_format)
            sheet.write(row, 3, company_name, normal_format)
            row += 1
            
            sheet.write(row, 1, 'Property Manager', label_format)
            sheet.write(row, 3, property_manager, normal_format)
            row += 1
            
            sheet.write(row, 1, 'Parent Property', label_format)
            sheet.write(row, 3, parent_prop_name, normal_format)
            row += 1

            row += 1  # Spacing

            # Note in yellow
            sheet.merge_range(row, 1, row, 13, 'Show special units in each building in a separate and ordered table', note_format)
            row += 1

            # Table Headers
            headers = ['NO', 'Properties', 'Property Type', 'Auto - Address No', 'Tenancy Name', 'Tenant', 'Phone', 'Tenancy Rent', 'Tenancy States', 'Legal Case', 'Tenancy Date', 'Start Date', 'Expiration Date', 'Close Date']
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)
            row += 1

            # Write properties
            count = 1
            for prop in properties:
                sheet.write(row, 0, count, center_border)
                sheet.write(row, 1, prop.get('property_name', ''), normal_format)
                sheet.write(row, 2, prop.get('property_type', ''), normal_format)
                sheet.write(row, 3, prop.get('auto_address_no', ''), center_border)
                
                # Contract data - show only if active contract exists
                if prop.get('has_active_contract'):
                    sheet.write(row, 4, prop.get('tenancy_name', ''), normal_format)
                    sheet.write(row, 5, prop.get('tenant', ''), normal_format)
                    sheet.write(row, 6, prop.get('phone', ''), normal_format)
                    sheet.write(row, 7, prop.get('tenancy_rent', 0.0), money_cell_format)
                    sheet.write(row, 8, prop.get('tenancy_states', ''), center_border)
                    # New fields after tenancy_states
                    legal_case = 'Legal Case' if prop.get('legal_case') else ''
                    sheet.write(row, 9, legal_case, center_border)
                    # Handle dates - convert to string if they're date objects
                    tenancy_date = prop.get('tenancy_date', '')
                    if tenancy_date:
                        if isinstance(tenancy_date, str):
                            sheet.write(row, 10, tenancy_date, normal_format)
                        else:
                            sheet.write(row, 10, tenancy_date, date_format)
                    else:
                        sheet.write(row, 10, '', normal_format)
                    start_date = prop.get('start_date', '')
                    if start_date:
                        if isinstance(start_date, str):
                            sheet.write(row, 11, start_date, normal_format)
                        else:
                            sheet.write(row, 11, start_date, date_format)
                    else:
                        sheet.write(row, 11, '', normal_format)
                    expiration_date = prop.get('expiration_date', '')
                    if expiration_date:
                        if isinstance(expiration_date, str):
                            sheet.write(row, 12, expiration_date, normal_format)
                        else:
                            sheet.write(row, 12, expiration_date, date_format)
                    else:
                        sheet.write(row, 12, '', normal_format)
                    close_date = prop.get('close_date', '')
                    if close_date:
                        if isinstance(close_date, str):
                            sheet.write(row, 13, close_date, normal_format)
                        else:
                            sheet.write(row, 13, close_date, date_format)
                    else:
                        sheet.write(row, 13, '', normal_format)
                else:
                    # Empty contract data cells with yellow background
                    for col in range(4, 14):
                        sheet.write(row, col, '', workbook.add_format({'bg_color': '#FFFF00', 'border': 1}))

                row += 1
                count += 1
           
            # Conditional note in yellow
            sheet.merge_range(row, 1, row, 13, 'In case there is no active contract during the period required by the report for the unit, the unit will appear with empty contract data', note_format)
            row += 2  # Spacing after group

        workbook.close()
        output.seek(0)
        return output.read()

    def action_generate_report(self):
        # Generate report
        report_data = self.generate_xlsx_report()

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Property_with_Contracts_Report.xlsx',
            'datas': base64.encodebytes(report_data),
            'type': 'binary',
            'res_model': self._name,
            'res_id': self.id,
        })

        # Trigger download
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }

class PropertyContractsReport(models.AbstractModel):
    _name = "report.mm_property_inherit_new.tem_property_contracts_report_id"

    @api.model
    def _get_report_values(self, docids, data=None):
        # Handle date parsing - dates can come as strings or Date objects
        from_date_val = data['form'].get('from_date', '')
        to_date_val = data['form'].get('to_date', '')
        
        # Parse dates - handle both string and date object formats
        if from_date_val:
            if isinstance(from_date_val, str) and from_date_val:
                from_date = datetime.strptime(from_date_val, '%Y-%m-%d').date()
            elif isinstance(from_date_val, date):
                from_date = from_date_val
            else:
                from_date = None
        else:
            from_date = None
            
        if to_date_val:
            if isinstance(to_date_val, str) and to_date_val:
                to_date = datetime.strptime(to_date_val, '%Y-%m-%d').date()
            elif isinstance(to_date_val, date):
                to_date = to_date_val
            else:
                to_date = None
        else:
            to_date = None
        
        # Build domain for properties
        domains = []
        if data['form'].get('company_id'):
            domains.append(('company_id.name', '=', data['form']['company_id']))
        if data['form'].get('property_manager_id'):
            domains.append(('property_manager.name', '=', data['form']['property_manager_id']))
        if data['form'].get('parent_property_id'):
            domains.append(('parent_id.name', '=', data['form']['parent_property_id']))
        
        # Get all properties (not just those with contracts)
        properties = self.env['account.asset'].search(domains)
        properties = sorted(properties, key=lambda r: (r.id or 0))

        # Group properties by parent property
        grouped_data = {}
        
        for prop in properties:
            # Skip parent properties (only process child properties)
            if prop.parent_id:
                parent_name = prop.parent_id.name
                
                if parent_name not in grouped_data:
                    grouped_data[parent_name] = {
                        'company_name': prop.company_id.name if prop.company_id else '',
                        'property_manager': prop.property_manager.name if prop.property_manager else '',
                        'properties': []
                    }
                
                # Check for active tenancy in date range
                # A tenancy is considered "active during the period" if:
                # 1. It has started on or before the end date (to_date)
                # 2. It has not ended before the start date (from_date), or has no end date
                active_tenancy = None
                
                # Get all tenancies sorted by date (most recent first)
                all_tenancies = prop.tenancy_property_ids.sorted('date', reverse=True)

                # Filter by date range if provided
                if from_date and to_date:
                    for tenancy in all_tenancies:
                        # Get tenancy dates
                        tenancy_start = tenancy.date if tenancy.date else None
                        tenancy_end = tenancy.close_date if tenancy.close_date else None
                        
                        if not tenancy_start:
                            continue  # Skip tenancies without start date
                        
                        # Check if tenancy was active during the specified date range
                        # Tenancy is active if it overlaps with the date range:
                        # - Started before or during the range (tenancy_start <= to_date)
                        # - Hasn't ended before the range starts (tenancy_end is None OR tenancy_end >= from_date)
                        started_in_range = tenancy_start <= to_date
                        not_ended_before_range = tenancy_end is None or tenancy_end >= from_date
                        
                        if started_in_range and not_ended_before_range:
                            active_tenancy = tenancy
                            break
                elif all_tenancies:
                    # If no date range specified, get the most recent active (open/pending) tenancy
                    # or the most recent tenancy if no active ones
                    active_tenancies = all_tenancies.filtered(lambda t: t.state in ['open', 'pending'])
                    if active_tenancies:
                        active_tenancy = active_tenancies[0]
                    else:
                        # If no active tenancies, use the most recent one anyway
                        active_tenancy = all_tenancies[0]
                
                # Build property data
                property_name = prop.multi_properitis if hasattr(prop, 'multi_properitis') and prop.multi_properitis else prop.name
                prop_data = {
                    'property_name': property_name,
                    'property_type': prop.type_id.name if prop.type_id else '',
                    'auto_address_no': str(prop.auto_add_no) if hasattr(prop, 'auto_add_no') and prop.auto_add_no else '',
                    'has_active_contract': bool(active_tenancy),
                }
                
                # Add contract data if active contract exists
                if active_tenancy:
                    prop_data.update({
                        'tenancy_name': active_tenancy.code if active_tenancy.code else '',
                        'tenant': active_tenancy.tenant_id.name if active_tenancy.tenant_id else '',
                        'phone': active_tenancy.tenant_id.phone if active_tenancy.tenant_id and active_tenancy.tenant_id.phone else '',
                        'tenancy_rent': active_tenancy.rent if active_tenancy.rent else 0.0,
                        'tenancy_states': active_tenancy.state if active_tenancy.state else '',
                        'legal_case': active_tenancy.legal_case if hasattr(active_tenancy, 'legal_case') and active_tenancy.legal_case else False,
                        'tenancy_date': active_tenancy.date if active_tenancy.date else '',
                        'start_date': active_tenancy.date_start if hasattr(active_tenancy, 'date_start') and active_tenancy.date_start else (active_tenancy.date if active_tenancy.date else ''),
                        'expiration_date': active_tenancy.date if active_tenancy.date else '',
                        'close_date': active_tenancy.close_date if active_tenancy.close_date else '',
                    })
                else:
                    prop_data.update({
                        'tenancy_name': '',
                        'tenant': '',
                        'phone': '',
                        'tenancy_rent': 0.0,
                        'tenancy_states': '',
                        'legal_case': False,
                        'tenancy_date': '',
                        'start_date': '',
                        'expiration_date': '',
                        'close_date': '',
                    })
                
                grouped_data[parent_name]['properties'].append(prop_data)
            
            # Sort properties within each group by name
        for parent_name in grouped_data:
            grouped_data[parent_name]['properties'].sort(key=lambda x: x.get('property_name', ''))
        
        # Build flat docs list for PDF (maintain backward compatibility)
        docs = []
        for parent_name, group_info in grouped_data.items():
            for prop in group_info['properties']:
                
                docs.append({
                        'doc_ids': data.get('ids', []),
                        'doc_model': data.get('model', ''),
                        'parent_id': parent_name,
                        'company_name': group_info['company_name'],
                        'property_manager': group_info['property_manager'],
                        'properties': prop['property_name'],
                        'property_type': prop['property_type'],
                        'auto_address_no': prop['auto_address_no'],
                        'tenancy_name': prop['tenancy_name'],
                        'tenant': prop['tenant'],
                        'phone': prop['phone'],
                        'tenancy_rent': prop['tenancy_rent'],
                        'tenancy_states': prop['tenancy_states'],
                        'has_active_contract': prop['has_active_contract'],
                        'legal_case': prop.get('legal_case', False),
                        'tenancy_date': prop.get('tenancy_date', ''),
                        'start_date': prop.get('start_date', ''),
                        'expiration_date': prop.get('expiration_date', ''),
                        'close_date': prop.get('close_date', ''),


                    })
            
        # Get unique parent names for iteration
        parent_dict2 = list(grouped_data.keys())
        
        # Get the wizard record for the template (o object required by web.external_layout)
        # docids should contain the wizard record IDs
        if docids:
            wizard_records = self.env['property.contracts.report.wiz'].browse(docids)
            wizard_record = wizard_records[0] if wizard_records else None
        else:
            wizard_record = None
        
        # If no wizard record, create a dummy one (shouldn't happen in normal flow)
        if not wizard_record:
            # Use the first company's recordset as a fallback for company context
            wizard_record = self.env['property.contracts.report.wiz'].new({})

        return {
            'o': wizard_record,  # Required by web.external_layout - must be a record, not dict
            'docs': docs,
            'parent_dict2': parent_dict2,
            'grouped_data': grouped_data,  # For Excel export
        }
