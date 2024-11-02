# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Management - Odoo Community Compatible (Without Portal)',
    'version': '0.1',
    'category': 'Real Estate',
    'license': 'LGPL-3',
    'summary': """
        property management
        asset management
        tenancy tenant contract
        recurring contract
        penalty maintenance management
        property sale purchase
        booking management
        property rent sale purchase
     """,
    'description': """
        property management
        asset management
        tenancy tenant contract
        recurring contract
        penalty maintenance management
        property sale purchase
        booking management
        property rent sale purchase
     """,
    'sequence': 1,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.in/product/property-management-system',
    'depends': [
        'property_management',
        'property_recurring_maintenance',
        'property_penalty',
        'property_sale_purchase',
        'property_rent_report',
        'property_booking',
        'property_landlord_management',
        'property_maintenance',
        'multiple_property_rent',
        'property_commission',
        'property_auto_invoice'
    ],
    'images': ['static/description/Property-Management-System-banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price': 9,
    'currency': 'EUR',
}
