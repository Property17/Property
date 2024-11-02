# See LICENSE file for full copyright and licensing details

{
    'name': 'Property Maintenance',
    'version': '0.1',
    'category': 'Real Estate',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': """
            You can manage maintenance of property
            maintenance management
            building maintenance
            maintenance schedule
            maintenance calendar
            maintenance process
            maintenance statistics
    """,
    'license': 'LGPL-3',
    'website': 'https://www.serpentcs.in/product/property-management-system',
    'depends': ['property_management','base','maintenance'],
    'data': [
        'security/maint_security.xml',
        'security/ir.model.access.csv',
        'data/maintenanse_data_stage.xml',
        'data/mail_maintenance_template.xml',
        'views/asset_management_view.xml',
        'views/maintenance_view.xml',
    ],
    'images': ['static/description/Property-Maintance-banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 99,
    'currency': 'EUR',
}
