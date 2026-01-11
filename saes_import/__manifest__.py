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
        "views/saes_menu.xml",
        "views/saes_table_selector_views.xml",
        "views/saes_client_preview_wizard.xml",
        "views/saes_detected_tables_wizard.xml"
    ],
    "installable": True,
    "application": False,
}
