# See LICENSE file for full copyright and licensing details

{
    'name': 'Property Automatic Invoice',
    'version': '0.1',
    'category': 'Real Estate',
    'license': 'LGPL-3',
    'summary': """
        Automatic create invoice for property
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.in/product/property-management-system',
    'depends': ['property_management'],
    'data': [
        'data/scheduler_auto_invoice.xml',
        'views/res_config_settings_views.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price': 99,
    'currency': 'EUR',
}
