# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Booking',
    'version': '0.1',
    'category': 'Real Estate',
    'summary': """
        Property Management Booking System
        Booking management
        flat booking
        office booking
        apartment booking
    """,
    'description': """
        Property Management Booking System
        Booking management
        flat booking
        office booking
        apartment booking
    """,
    'license': 'LGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://serpentcs.in/product/property-management-system',
    'depends': ['property_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/view_property_booking.xml',
        'wizard/view_merge_property_wizard.xml',
        'wizard/view_property_book_wizard.xml',
    ],
    'images': ['static/description/Property Booking_banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 99,
    'currency': 'EUR',
}
