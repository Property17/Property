# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import  timedelta


class PropertyAvailableWiz(models.TransientModel):
    
    _name = 'property.available.wiz'

    def _default_from_date(self):
        return fields.Date.context_today(self) - timedelta(days=7)

    def _default_to_date(self):
        return fields.Date.context_today(self)


    company_id = fields.Many2one('res.company', string='Company')
    property_manager_id = fields.Many2one('res.partner', domain="[('is_manager', '=', True), ('company_id', '=', company_id)]", string='Property Manager')
    parent_property_id = fields.Many2one('account.asset', domain="[('parent_id', '=', False), ('property_manager', '=', property_manager_id)]", string='Parent Property')


  
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'company_id': self.company_id.name,
                'property_manager_id': self.property_manager_id.name,
                'parent_property_id': self.parent_property_id.name,
            },
        }
        return self.env.ref('mm_property_inherit_new.report_property_available_id').report_action(self, data=data)
    
    
    def get_tree_report(self):
        domains = [('state', '=', 'draft')] 

        if self.company_id:
            domains.append(('company_id', '=', self.company_id.id))
        if self.property_manager_id:
            domains.append(('property_manager', '=', self.property_manager_id.id))
        if self.parent_property_id:
            domains.append(('parent_id', '=', self.parent_property_id.id))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Available Properties'),
            'res_model': 'account.asset',
            'view_mode': 'tree,form', 
            'domain': domains,
            'context': {
                'search_default_grpstate': 1,
                'default_is_property': True,
            },
            'views': [
                (self.env.ref('property_management.property_view_asset_tree').id, 'tree'),
                (self.env.ref('property_management.property_asset_form').id, 'form'),

            ],
        }




class PropertyAvailableReport(models.AbstractModel):
    _name = "report.mm_property_inherit_new.tem_property_ava_id"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        domains = []

        # if data['form']['from_date']:
        #     domains.append(('date', '>=', data['form']['from_date']))
        # if data['form']['to_date']:
        #     domains.append(('date', '<=', data['form']['to_date']))
        if data['form']['company_id']:
            domains.append(('company_id.name', '=', data['form']['company_id']))
        if data['form']['property_manager_id']:
            domains.append(('property_manager.name', '=', data['form']['property_manager_id']))
        if data['form']['parent_property_id']:
            domains.append(('parent_id.name', '=', data['form']['parent_property_id']))
    
        records = self.env['account.asset'].search(domains)
        
        for rec in records:
            last_tenancy = rec.tenancy_property_ids.sorted(lambda t: t.date, reverse=True)[:1]
            if rec.state == 'draft':
                docs.append({
                    'doc_ids': data['ids'],
                    'doc_model': data['model'],
                    'properties': rec.name,
                    'property_type': rec.type_id.name,
                    'auto_address_no': rec.auto_add_no,
                    'address': rec.street,
                    'last_tenancy_rant_amount': last_tenancy.rent if last_tenancy else 0.0,
                    'Last_close_date': last_tenancy.close_date if last_tenancy else '', 
                })
            
        return {
            'docs': docs,
        }
    
    