# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import  timedelta


class TenancyExpiryWiz(models.TransientModel):
    
    _name = 'tenancy.expiry.wiz'

    def _default_from_date(self):
        return fields.Date.context_today(self) - timedelta(days=7)

    def _default_to_date(self):
        return fields.Date.context_today(self)

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    company_id = fields.Many2one('res.company', string='Company')
    property_manager_id = fields.Many2one('res.partner', domain="[('is_manager', '=', True), ('company_id', '=', company_id)]",  string='Property Manager')

  
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'from_date': self.from_date,
                'to_date': self.to_date,
                'company_id': self.company_id.name,
                'property_manager_id': self.property_manager_id.name,
            },
        }
        return self.env.ref('mm_property_inherit_new.report_tenancy_expiry_id').report_action(self, data=data)
    
    
    
        
    def get_tree_report(self):
        domains = [('is_property', '=', True),('state', '!=', 'close')]

        if self.company_id:
            domains.append(('company_id', '=', self.company_id.id))
        if self.property_manager_id:
            domains.append(('property_manager', '=', self.property_manager_id.id))
        if self.from_date:
            domains.append(('date', '>=', self.from_date))
        if self.to_date:
            domains.append(('date', '<=', self.to_date))
            

        return {
            'type': 'ir.actions.act_window',
            'name': _('Tenancy Expiry'),
            'res_model': 'account.analytic.account',
            'view_mode': 'tree,form', 
            'domain': domains,
            'context': {
                'default_is_property': True,
                'default_resident_type': 'tenant_tenancy',
            },
            'views': [
                    (self.env.ref('property_management.property_analytic_view_tree').id, 'tree'),
                    (self.env.ref('property_management.property_analytic_view_form').id, 'form'),

                ],

        }



class TenancyExpiryReport(models.AbstractModel):
    _name = "report.mm_property_inherit_new.tem_tenancy_exp_id"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        domains = []

        if data['form']['from_date']:
            domains.append(('date', '>=', data['form']['from_date']))
        if data['form']['to_date']:
            domains.append(('date', '<=', data['form']['to_date']))
        if data['form']['company_id']:
            domains.append(('company_id.name', '=', data['form']['company_id']))
        if data['form']['property_manager_id']:
            domains.append(('property_manager_id.name', '=', data['form']['property_manager_id']))
    
        records = self.env['account.analytic.account'].search(domains)
        
        for rec in records:
            if rec.state != 'close':
                docs.append({
                    'doc_ids': data['ids'],
                    'doc_model': data['model'],
                    'parent_property': rec.property_id.parent_id.name,
                    'properties': rec.multi_properitis,
                    'tenancy': rec.code,
                    'tenant': rec.tenant_id.name,
                    'tenancy_rent': rec.rent,
                    'expiration_date': rec.date,
                })
            
        return {
            'docs': docs,
        }
    
    