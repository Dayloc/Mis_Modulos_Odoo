{
    "name": "Compras e Inventario Personalizado",
    "version": "1.0",
    "category": "Purchases",
    "summary": "Personalizaciones para los módulos de Compras e Inventario",
    "description": """
                                      Este módulo permite personalizar el comportamiento de:
                                      - Órdenes de compra
                                      - Recepciones de inventario
                                      """,
    "author": "Dayloc",
    "depends": [
        "purchase",
        'purchase_stock',
        "stock",
        "project",
        "account",

    ],
    'assets': {
        'web.assets_backend': [
            'custom_compras_inventario/static/src/css/center_project_column.css',
             "custom_compras_inventario/static/src/components/project_dashboard/project_dashboard_inject.js",

        ],

    },
    "data": [
        "views/stock_move_gastos_view.xml",
        "views/orden_compra_view.xml",
        "views/project_gastos_action.xml",
        "views/project_form_view.xml",
        "views/inventario_view.xml",
        "views/project_view.xml",


    ],
    "installable": True,
    "application": False
}
