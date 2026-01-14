{
    "name": "SAGES Importador",
    "version": "1.0.0",
    "category": "Tools",
    "summary": "Importación de datos desde SAGE hacia Odoo",
    "description": """
                                                         Módulo para importar datos desde SAGES (clientes, direcciones, proveedores,pedidos,facturas)
                                                         de forma parametrizable y controlada.
                                                             """,
    "author": "Dayloc",
    "depends": [
        "base",
        "contacts",
        'product',
        'stock',
        "purchase",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/saes_config_view.xml",
        "views/buttons_menu.xml",
        "views/res_partner_view.xml",
        "views/table_clients_selector_views.xml",
        "views/clients_table_preview_wizard.xml",
        "views/detected_all_tables_wizard.xml",
        "views/provider_table_selector.xml",
        "views/product_table_selector_view.xml",
        "views/sale_order_table_selector_view.xml",
        "views/wizard_preview_provider_view.xml",
        "views/product_preview_wizard.xml",

    ],
    "installable": True,
    "application": True,
}
