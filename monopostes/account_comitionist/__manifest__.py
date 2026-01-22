# -*- coding: utf-8 -*-
{
    'name': 'Account Comitionist',
    'version': '1.0',
    'summary': 'Brief description of the module',
    'description': '''
        Detailed description of the module
    ''',

    'depends': ['base', 'account', 'custom_comisionista_report'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_comitionist_views.xml',
		'views/account_move_inherit.xml',
		'views/action_account_move.xml',
],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}