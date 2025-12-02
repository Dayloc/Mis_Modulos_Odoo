# -*- coding: utf-8 -*-
{
    'name': 'Activia Products',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Activia Products',
    'description': '''Ventas de productos peligrosos y exclusivos''',
    'author': 'Activia Products',
    'website': 'https://www.ActiviaProducts.com',
    'depends': ['base', 'sale', 'product', 'contacts'],
    'data': [
        'views/res_partner_templates.xml',
        'views/product_template_views.xml',
        'views/res_partner_views.xml',
        'security/ir.model.access.csv',    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
