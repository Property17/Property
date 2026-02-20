# -*- coding: utf-8 -*-
{
    'name': "property_payment_link",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Faisal Elmubarak",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['property_management', 'website', 'portal', 'pyment_report', 'mail', 'whatsapp'],

    # always loaded
    'data': [
        'data/whatsapp_template_action.xml',
        'security/ir.model.access.csv',
        'views/payment_link.xml',
        'views/payment_link_templates.xml',
        'views/view_account_analytic.xml',
        'reports/invoice_report.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'assets': {
        'web.assets_frontend': [
            'property_payment_link/static/src/css/payment_link.css',
            'property_payment_link/static/src/components/**/*',
            'property_payment_link/static/src/js/payment_form_extend.js',
        ]
    },
}

