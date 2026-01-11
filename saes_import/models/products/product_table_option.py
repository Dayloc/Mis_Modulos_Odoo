from odoo import models, fields

class ProductTableOption(models.TransientModel):
    _name = "product.table.option"
    _description = "Tabla candidata de productos"

    name = fields.Char(string="Tabla", required=True)

    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade",
    )
