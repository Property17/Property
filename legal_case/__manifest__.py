# -*- coding: utf-8 -*-
{
    'name': "Legal case Custom Module",

    'summary': """
       Legal case Custom Module""",

    'description': """
      Legal case  Custom  Module
    """,

    'author': "Anas",

    # 'category': 'account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','property_management'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/views.xml',
        'views/legal_case_request_view.xml',
        'views/legal_case_view.xml',
        'views/menus.xml',
    ],
   
}
