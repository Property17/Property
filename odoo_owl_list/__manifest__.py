# -*- coding: utf-8 -*-
{
    'name': "Odoo OWL JS",
    'summary': "Odoo OWL JS",
    'description': "Odoo OWL JS",
    'author': "Anas",
    'version': '0.1',
    'sequence': 1,
    'depends': ['web','property_management','mm_property_inherit_new'],
    'data': [
        'tenancy.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_owl_list/static/src/js/list_controller.js',
            'odoo_owl_list/static/src/xml/list_controller.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
