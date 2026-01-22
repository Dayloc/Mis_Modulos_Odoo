{
    'name': "Custom Reports Monoposte",
    'summary': "Adds new custom report layouts to Odoo",
    'version': '1.0',
    'category': 'Reporting',
    'depends': ['web','account','sale'],
    'data': [
        'views/report_templates.xml',
        'data/report_layout_data.xml',
        'views/report_invoice_custom.xml',
        'views/report_saleorder_custom.xml',
    ],
    'installable': True,
    'auto_install': False,
}
