{
    'name': 'CNAE 2025',
    'version': '18.0.1.0.0',
    'category': 'Contacts',
    'summary': 'Clasificación CNAE 2025 para contactos',
    'author': 'Generic',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cnae_views.xml',
        'views/cnae_menu.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': False,
}
