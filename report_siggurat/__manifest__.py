{
    'name': "Informe de Venta Personalizado (Siggurat)",
    'summary': "Genera un PDF de venta con el formato del presupuesto Siggurat.",
    'version': '1.0',
    'category': 'Sales',
    'depends': ['sale_management', 'web'], # Dependemos del módulo de Ventas
    'data': [
        # 'security/ir.model.access.csv', # Necesario si añades modelos nuevos (no es el caso aquí)
        'views/report_actions.xml',     # Define la acción de imprimir
        # 'views/report_puentia_views.xml',    # Define el diseño (la parte importante)
        'views/report_invoice_siggurat.xml',    # Define el diseño (la parte importante)
        # 'views/sale_copy_report.xml',    # Define el diseño (la parte importante)

    ],
    'installable': True,
}