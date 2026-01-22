{
    'name': 'Extensión de Reporte de Presupuesto',
    'version': '1.0',
    'depends': ['project', 'account', 'account_accountant', 'account_budget'], # Ajusta según tus dependencias reales
    'data': [
        'views/budget_report_views.xml',
    ],
    'installable': True,
}