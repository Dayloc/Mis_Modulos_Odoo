from odoo import models, fields


class SaesClientTableOption(models.TransientModel):
    _name = "saes.client.table.option"
    _description = "Tabla candidata de clientes"

    name = fields.Char(string="Tabla", required=True)

    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade",
    )
