from odoo import models, fields
from odoo.exceptions import UserError

class ProductTableSelector(models.TransientModel):
    _name = "product.table.selector"
    _description = "Selector de tabla de productos"

    table_id = fields.Many2one(
        "product.table.option",
        string="Tabla de productos",
        required=True,
        ondelete="cascade",
    )

    def action_confirm(self):
        self.ensure_one()

        config = self.env["saes.import.config"].browse(
            self.env.context.get("active_id")
        )

        if not config:
            raise UserError("No se encontró la configuración activa.")

        config.product_table = self.table_id.name

        return {"type": "ir.actions.act_window_close"}
