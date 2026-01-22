# -*- coding: utf-8 -*-
{
    'name': 'Reporte de Beneficios de Emplazamientos',
    'version': '1.0',
    'summary': 'Genera reportes de beneficios basados en ventas por emplazamiento.',
    'description': """
        Este módulo complementa mp_site para ofrecer un análisis financiero.
        Calcula ingresos y comisiones basándose en las líneas de pedido de venta 
        que coinciden con los nombres de los espacios publicitarios de cada emplazamiento.
    """,
    'category': 'Reporting',
    'author': 'Tu Nombre',
    'depends': ['base', 'sale_management', 'mp_site'],
    'data': [
        'security/ir.model.access.csv',
        'views/benefit_report_views.xml',
        'report/benefit_report_template.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}