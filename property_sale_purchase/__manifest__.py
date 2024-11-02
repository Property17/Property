# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Sales And Purchase',
    'version': '0.1',
    'category': 'Real Estate',
    'summary': """
        Property Sales And Purchase
        Asset sales purchase
        real estate sale purchase
        building sale purchase
     """,
    'license': 'LGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.in/product/property-management-system',
    'depends': ['property_management'],
    'data': [
        'security/ir.model.access.csv',
        'report/investment_report_view.xml',
        # 'views/sale_purchase_asset.xml',
    ],
    'images': ['static/description/Property-Sales-And-Purchase-banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price': 99,
    'currency': 'EUR',
}
