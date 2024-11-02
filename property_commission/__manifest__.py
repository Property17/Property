# See LICENSE file for full copyright and licensing details

{
    'name': 'Commission Management for Property Management System',
    'version': '0.1',
    'category': 'Real Estate',
    'summary': """
        property commission
        asset commission
        tenancy commission
        tenant commission
        Commission Management for Property Management
     """,
    'description': """
        property commission
        asset commission
        tenancy commission
        tenant commission
        Commission Management for Property Management
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.in/product/property-management-system',
    'depends': ['property_management'],
    'data': [
            'data/commission_seq.xml',
            'security/res_groups.xml',
            'security/ir.model.access.csv',
            'views/property_commission_view.xml',
            'views/property_res_partner_views.xml',
            'report/commission_report_template2.xml',
            # 'views/report_configuration.xml',

    ],
    'images': ['static/description/Commission-Management-for-Property-Management-System-banner.png'],
    'license': 'LGPL-3',
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 99,
    'currency': 'EUR',
}
