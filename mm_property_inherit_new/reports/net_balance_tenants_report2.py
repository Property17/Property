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

class NetBalanceTenantsWiz(models.TransientModel):
    
    _name = 'net.balance.tenants.wiz'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    company_id = fields.Many2one('res.company', string='Company')
    property_manager_id = fields.Many2one('res.partner', domain="[('is_manager', '=', True), ('company_id', '=', company_id)]", string='Property Manager')
    parent_property_id = fields.Many2one('account.asset', domain="[('parent_id', '=', False), ('property_manager', '=', property_manager_id)]", string='Parent Property')
    include_initial_balance = fields.Boolean('Include initial balance')
    
    @api.onchange('from_date', 'to_date')
    def _onchange_set_include_initial_balance(self):
        if self.from_date and self.to_date:
            self.include_initial_balance = True
        else:
            self.include_initial_balance = False

  
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'from_date': self.from_date,
                'to_date': self.to_date,
                'company_id': self.company_id.name,
                'property_manager_id': self.property_manager_id.name,
                'parent_property_id': self.parent_property_id.name,
            },
        }
        return self.env.ref('mm_property_inherit_new.report_net_balance_tenants_id').report_action(self, data=data)
    
    def generate_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Net Balance Tenants')
        sheet.set_zoom(90)

        # Column widths
        column_widths = [6, 20, 25, 15, 20, 15, 10, 15, 10, 15, 15, 15, 18]  # Increased last column to width 18

        for i, width in enumerate(column_widths):
            sheet.set_column(i, i, width)

        # Formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 13,
            'align': 'center',
            'valign': 'vcenter',
        })
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 13,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        bold_center = workbook.add_format({'bold': True, 'align': 'center'})
        date_format = workbook.add_format({'num_format': 'dd-mm-yyyy', 'align': 'center','border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        normal_format = workbook.add_format({'align': 'left', 'border': 1})
        money_cell_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'border': 1})
        number_format = workbook.add_format({'num_format': '#0', 'align': 'right', 'border': 1})
        center_border = workbook.add_format({'align': 'center', 'border': 1})
        parent_title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 13,
            'valign': 'vcenter'
        })
        label_bold_13 = workbook.add_format({
            'bold': True,
            'font_size': 13,
            'align': 'left'
        })
        total_label_format = workbook.add_format({'bold': True, 'align': 'right', 'border': 1})
        total_money_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'align': 'right', 'border': 1})



        # Header info
        sheet.merge_range('A1:L1', 'تقرير ارصدة المستاجرين', title_format)
        sheet.write('A2', 'تاريخ الطباعة:', bold_center)
        sheet.write('B2', fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        
        row = 3
        if self.from_date:
            sheet.merge_range(row, 0, row, 1, 'من تاريخ:', label_bold_13)
            sheet.merge_range(row, 2, row, 4, self.from_date, date_format)
            row += 1
        if self.to_date:
            sheet.merge_range(row, 0, row, 1, 'الي تاريخ', label_bold_13)
            sheet.merge_range(row, 2, row, 4, self.to_date, date_format)
            row += 1
        if self.company_id:
            sheet.merge_range(row, 0, row, 1, 'الشركة', label_bold_13)
            sheet.merge_range(row, 2, row, 4, self.company_id.name)
            row += 1
        if self.property_manager_id:
            sheet.merge_range(row, 0, row, 1, 'المدير العقاري ', label_bold_13)
            sheet.merge_range(row, 2, row, 4, self.property_manager_id.name)
            row += 1
        if self.parent_property_id:
            sheet.merge_range(row, 0, row, 1, 'البناية', label_bold_13)
            sheet.merge_range(row, 2, row, 4, self.parent_property_id.name)
            row += 1

        row += 2  # spacing

        # Fetch data like in PDF
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

        report_data = self.env['report.mm_property_inherit_new.tem_net_balance_ten_id']._get_report_values(self.ids, data)
        docs = report_data.get('docs', [])
        parent_names = report_data.get('parent_dict2', [])

        headers = ['رقم', 'الوحدة', 'المستأجر', ' رقم الهاتف', 'العقد', 'قيمة العقد',
                'حالة العقد', 'تاريخ الاغلاق', 'الحالة القضائية','الأشهر المستحقة',   'رصيد مرحل',  'الرصيد','الاستحقاق','التسديد', 'اجمالي الأرصدة']
        
        for parent_name in parent_names:
            group_initial = 0.0
            group_balance = 0.0
            group_total = 0.0
            balance_accurate = 0.0
            balance_advanced = 0.0
            month_due = 0
            group_debit = 0.0  # NEW
            group_credit = 0.0  # NEW

            count = 1
            # Write parent title
            # sheet.merge_range(row, 0, row, len(headers) - 1, parent_name, bold_center)
            sheet.merge_range(row, 0, row, len(headers) - 1, parent_name, parent_title_format)
            row += 1

            # Write table headers
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)
            row += 1


            for rec in docs:
                if rec.get('parent_id') != parent_name:
                    continue
                
                total_balance = rec.get('total_balance') or 0.0
                balance = rec.get('balance') or 0.0

                if total_balance == 0.0 and balance == 0.0:
                    continue 
                
                rent = rec.get('tenancy_rent') or 0
                # month_due = int(total_balance / rent)
                # month_due = math.ceil(total_balance / rent)
                 # Avoid division by zero
                if rent <= 0:
                    month_due = 0
                else:
                    month_due = math.ceil(total_balance / rent)

                
                sheet.write(row, 0, count, center_border)
                sheet.write(row, 1, rec.get('properties') or '', normal_format)
                sheet.write(row, 2, rec.get('tenant_id') or '', normal_format)
                sheet.write(row, 3, rec.get('phone') or '', normal_format)
                sheet.write(row, 4, rec.get('tenancy_id') or '', normal_format)
                sheet.write(row, 5, rec.get('tenancy_rent') or 0.0, money_cell_format)
                sheet.write(row, 6, rec.get('state') or '', center_border)
                close_date = rec.get('close_date')
                sheet.write(row, 7, close_date if close_date else '', date_format)
                # sheet.write(row, 8, rec.get('legal') or '', center_border)
                legal = ''
                if rec.get('legal'):
                    legal = 'Legal'
                if rec.get('legal_case'):
                    legal = f"{legal}, Legal Case" if legal else 'Legal Case'
                sheet.write(row, 8, legal, center_border)
                sheet.write(row, 9, month_due or 0, number_format)
                sheet.write(row, 10, rec.get('initial_balance') or 0.0, money_cell_format)
                sheet.write(row, 11, rec.get('balance') or 0.0, money_cell_format)
                sheet.write(row, 12, rec.get('debit') or 0.0, money_cell_format)  # NEW
                sheet.write(row, 13, rec.get('credit') or 0.0, money_cell_format)  # NEW
                sheet.write(row, 14, rec.get('total_balance') or 0.0, money_cell_format)

                initial = rec.get('initial_balance') or 0.0
                balance = rec.get('balance') or 0.0
                debit = rec.get('debit') or 0.0  # NEW
                credit = rec.get('credit') or 0.0  # NEW
                total = rec.get('total_balance') or 0.0
 

                group_initial += initial
                group_balance += balance
                group_debit += debit  # NEW
                group_credit += credit  # NEW
                group_total += total
                balance_accurate +=  total if total > 0 else 0.0
                balance_advanced +=  total if total < 0 else 0.0

                row += 1
                count += 1
           
            # row += 1
            # Totals row
            sheet.write(row, 9, "الاجمالي", total_label_format)
            sheet.write(row, 10, group_initial,total_money_format)
            sheet.write(row, 11, group_balance,total_money_format)
            sheet.write(row, 12, group_debit, total_money_format)  # NEW
            sheet.write(row, 13, group_credit, total_money_format)  # NEW
            sheet.write(row, 14, group_total,total_money_format)
            row += 1  # space before next group
            
            sheet.write(row, 11, "الرصيد المستحق", total_label_format)
            sheet.write(row, 14, balance_accurate,total_money_format)
            row += 1  # space before next group
            sheet.write(row, 11, "الرصيد المقدم", total_label_format)
            sheet.write(row, 14, balance_advanced,total_money_format)
            
            row += 1  # spacing after each section
            
            

        workbook.close()
        output.seek(0)
        return output.read()
    


    def action_generate_report(self):
        # Generate report
        report_data = self.generate_xlsx_report()

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Net_Balance_Tenants_Report.xlsx',
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
        


     
class NetBalanceTenantsReport(models.AbstractModel):
    _name = "report.mm_property_inherit_new.tem_net_balance_ten_id"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        domains = []
      
        if data['form']['company_id']:
            domains.append(('company_id.name', '=', data['form']['company_id']))
        if data['form']['property_manager_id']:
            domains.append(('property_manager_id.name', '=', data['form']['property_manager_id']))
        if data['form']['parent_property_id']:
            domains.append(('property_id.parent_id.name', '=', data['form']['parent_property_id']))
        
        from_date_str = data['form'].get('from_date')
        to_date_str = data['form'].get('to_date')
        

        records = self.env['account.analytic.account'].search(domains)
        records = sorted(records, key=lambda r: (r.property_id.id or 0))

        if not records:
            return {'docs': []}

        # Domains for opening balance (before from_date)
        domains2 = [('move_id.state', '=', 'posted')]
        # domains2 = [('move_id.state', '=', 'posted')]
        if data['form']['from_date']:
            domains2.append(('move_id.date', '<', data['form']['from_date']))
            
        parent_propertites = self.env['account.asset'].search([('parent_id', '=', False)])

        parent_dict1 = []
        parent_dict2 = []

        for rec in records:
            parent_dict1.append(rec.property_id.parent_id.name)

        for rec2 in parent_propertites:
            if rec2.name in parent_dict1:
                parent_dict2.append(rec2.name)

        

        for rec in records:
            from_date_str = data['form'].get('from_date')
            to_date_str = data['form'].get('to_date')

            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date() if from_date_str else None
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date() if to_date_str else None

            # Filter balance lines based on date if given
            balance_lines = rec.account_move_line_debit_ids
            if from_date and to_date:
                balance_lines = balance_lines.filtered(lambda line: from_date <= line.date <= to_date)

            balance = sum(balance_lines.mapped('balance'))
            debit = sum(balance_lines.mapped('debit'))  # NEW
            credit = sum(balance_lines.mapped('credit'))  # NEW
                    
            opening_balance = 0.0
            if rec.tenant_id and from_date_str:
                move_lines = self.env['account.move.line'].search([
                    ('analytic_account_id', '=', rec.id),
                    ('partner_id', '=', rec.tenant_id.parent_id.id),  
                    *domains2,  
                ])
                opening_balance = sum(line.balance for line in move_lines) 
            else:
                opening_balance = 0.00
                
            total_balance = opening_balance + balance
            if rec.rent:
                month_due = math.ceil(total_balance / rec.rent)
            else:
                month_due = 0  


          
          
            docs.append({
                'doc_ids': data['ids'],
                'doc_model': data['model'],
                'properties': rec.multi_properitis,
                'tenant_id': rec.tenant_id.name,
                'phone': rec.tenant_id.phone,
                'tenancy_id': rec.code,
                'tenancy_rent': rec.rent,
                'state': rec.state,
                'close_date': rec.close_date,
                'legal': rec.legal,
                'legal_case': rec.legal_case,
                'month_due': month_due,
                'initial_balance': opening_balance,  
                'balance': balance,  
                'debit': debit,  # NEW
                'credit': credit,  # NEW
                'total_balance': opening_balance + balance,
                'parent_id': rec.property_id.parent_id.name

            })

        return {
            'docs': docs,
            'parent_dict2': parent_dict2,
        }
        
    
  
            
    