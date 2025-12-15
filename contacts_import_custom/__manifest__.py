{
    'name': 'Contacts Import Custom',
    'version': '1.0',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/import_contact_wizard_view.xml',
        'views/actions_menus.xml',
        'views/contact_views.xml',
    ],
     'installable': True,
    'application': True,
    'auto_install': False,
}

