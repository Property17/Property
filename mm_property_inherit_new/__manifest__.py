# -*- coding: utf-8 -*-
{
    'name': 'mm_property_inherit_new',
    'version': '0.1',
    'sequence': 1,
    'depends': ['base', 'property_management', 'account_asset', 'account', 'analytic'],
    'data': [
        'data/data2.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/property.xml',
        'views/property_custom.xml',
        'views/contract_template.xml',
        'views/contract.xml',
        'reports/contract_report.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
# test

}
