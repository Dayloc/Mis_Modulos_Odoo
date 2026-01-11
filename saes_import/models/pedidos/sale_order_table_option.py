from odoo import models, fields


class SaleOrderTableOption(models.TransientModel):
    _name = "sale.order.table.option"
    _description = "Tabla candidata de pedidos"

    name = fields.Char(
        string="Tabla",
        required=True
    )

    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade"
    )
