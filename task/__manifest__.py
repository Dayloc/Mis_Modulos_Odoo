# -*- coding: utf-8 -*-
{
    'name': 'Task',
    'version': '1.0',
    'summary': 'Brief description of the module',
    'description': '''
        Detailed description of the module
    ''',
    'category': 'Uncategorized',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail', 'contacts', 'sale'],
    'assets': {
        'web.report_assets_common': [
            'task/static/src/img/ziggurat_logo.png',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/task_views.xml',
        'views/res_partner_views.xml',
        'views/task_contacts_view_actions.xml',
        'views/task_views_actions.xml',
        'report/task_report_template.xml',
        'report/task_report.xml',
        'report/sale_custom_report_template.xml',
        'report/sale_custom_report.xml',
        'views/sale_order_report_button.xml',
        'views/view_task_menu.xml',

    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
