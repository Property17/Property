# -*- coding: utf-8 -*-
{
    'name': "pyment_report",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        'reports/payment_receipt_report.xml',
        # 'reports/invoice_report.xml',
        'reports/multi_invoice_report.xml',
        'reports/multi_deposite_report.xml',
        'reports/payment_deposite_report.xml',
        'views/account_payment.xml',
    ],
}
