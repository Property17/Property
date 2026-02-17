# -*- coding: utf-8 -*-
{
    'name': 'mm_property_inherit_new',
    'version': '0.1',
    'sequence': 1,
    'depends': ['base', 'property_management', 'account_asset', 'account', 'analytic','report_xlsx','account_reports'],
    'data': [
        'data/data2.xml',
        'data/cron.xml',
        'data/general_ledger_custom.xml',
        'security/ir.model.access.csv',
        'views/property.xml',
        'views/property_custom.xml',
        'views/contract_template.xml',
        'views/contract.xml',
        'reports/contract_report.xml',
        'reports/tenancy_expiry_wiz.xml',
        'reports/tenancy_exp_report_tem.xml',
        'reports/property_available_report_wiz.xml',
        'reports/property_available_tem.xml',
        # 'reports/invoice_report.xml',
        'reports/net_balance_tenants_wiz.xml',
        'reports/net_balance_tenants_report_tem.xml',
        'reports/property_with_contracts_report_wiz.xml',
        'reports/property_with_contracts_report_tem.xml',
        'views/discount.xml',
        'views/services_type.xml',        
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
# test

}
