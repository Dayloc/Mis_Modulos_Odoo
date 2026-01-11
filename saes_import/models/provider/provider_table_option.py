from odoo import models, fields


class SaesProviderTableOption(models.TransientModel):
    _name = "saes.provider.table.option"
    _description = "Tabla candidata de proveedores"

    name = fields.Char(string="Tabla", required=True)

    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade",
    )
