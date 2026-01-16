{
    'name': 'Reporte Mínimo',
    'version': '1.0',
    'summary': 'Reporte PDF básico desde cero',
    'author': 'Dayloc',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/reporte_min_report.xml',
        'report/reporte_min_template.xml',
        'views/reporte_min_view.xml',
    ],
    'installable': True,
    'application': True,
}
