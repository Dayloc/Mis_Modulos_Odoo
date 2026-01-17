from odoo import models, fields


class SaesSaleOrderLineTableOption(models.TransientModel):
    _name = "sale.order.line.table.option"
    _description = "Tabla candidata de líneas de pedido"

    name = fields.Char(string="Tabla", required=True)

    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade",
    )
