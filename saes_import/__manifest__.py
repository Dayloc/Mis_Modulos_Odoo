{
    "name": "SAES Importador",
    "version": "1.0.0",
    "category": "Tools",
    "summary": "Importación de datos desde SAE hacia Odoo",
    "description": """
                                      Módulo para importar datos desde SAE (clientes, direcciones, proveedores)
                                      de forma parametrizable y controlada.
                                          """,
    "author": "Dayloc",
    "depends": [
        "base",
        "contacts",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/saes_config_view.xml",
        "views/buttons_menu.xml",
        "views/table_clients_selector_views.xml",
        "views/clients_table_preview_wizard.xml",
        "views/detected_all_tables_wizard.xml",
        "views/provider_table_selector.xml",
        "views/product_table_selector_view.xml",
        "views/sale_order_table_selector_view.xml"
    ],
    "installable": True,
    "application": True,
}
