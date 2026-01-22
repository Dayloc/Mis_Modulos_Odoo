# -*- coding: utf-8 -*-
{
    'name': 'Gestión de Emplazamientos y Espacios Publicitarios',
    'version': '1.0',
    'summary': 'Módulo para gestionar emplazamientos de vallas y monopostes y sus espacios publicitarios.',
    'description': """
                           Este módulo permite gestionar la información de los terrenos donde se sitúan las vallas y monopostes (emplazamientos)
                           y los espacios publicitarios asociados a cada uno. Incluye funcionalidades para:
                           - Registro de emplazamientos con datos de ubicación, tipo, propiedad, contratos y presupuestos.
                           - Gestión de espacios publicitarios con identificador, dimensiones, visibilidad y estado.
                           - Relación entre emplazamientos y espacios publicitarios.
                           - Seguimiento de trabajos asociados, iluminación, y estados de disponibilidad.
                       """,
    'depends': [
        'base',
        'account',  # Para contratos y presupuestos si se vinculan directamente
        'hr',  # Para el campo 'Comercial' que es un usuario/empleado
        'sale_management',  # Dependencia del módulo de Ventas
        'project',  # Dependencia del módulo de Proyectos
        'sale_subscription',
        'purchase',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/res_users.xml',
        'views/action_server.xml',
        'views/emplacement_views.xml',
        'views/ad_space_views.xml',
        'views/ad_space_size_views.xml',
        'views/menu_views.xml',
        'views/project_project_views.xml',
        'data/dismantled_reason_data.xml',
        'views/emplacement_clock_views.xml',
        "views/dismantled_reason_views.xml",
        'views/emplacement_aux_data.xml',
        "views/emplacement_dismantled.xml",
        # 'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'data/mi_dato.xml',
        # Report de tareas
        'report/task_report_template.xml',
        'report/task_report.xml',
        # Report de bajas
        'report/sale_order_baja_report.xml',
        'report/report_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mp_site/static/src/css/ad_space_tree.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'icon': 'mp_site/static/description/icon.png',
    'license': 'LGPL-3',
}
