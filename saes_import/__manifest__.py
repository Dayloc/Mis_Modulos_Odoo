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
    ],
    "installable": True,
    "application": False,
}
