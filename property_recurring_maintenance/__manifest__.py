# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Recurring Maintenance',
    'version': '0.1',
    'category': 'Real Estate',
    'summary': """
        This module allows to manage the Recurring Maintenance
        maintenance subscription
        maintenance management
        maintenance charges and invoice
        maintenance account
     """,
    'license': 'LGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.in/product/property-management-system',
    'depends': ['property_maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'views/property_recuring_maintenance_view.xml'
    ],
    'images': ['static/description/Property-Recuring-Maintenance-banner.png'],
    'demo': ['data/recurring_maintenance_data.xml'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 99,
    'currency': 'EUR',
}
