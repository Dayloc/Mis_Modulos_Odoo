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

    def action_preview_raw(self):
        self.ensure_one()

        config = self.env["saes.import.config"].browse(
            self.env.context.get("active_id")
        )

        if not config:
            raise UserError("No hay configuración activa.")

        rows = config.preview_raw_table(self.table_id.name)

        if not rows:
            raise UserError("No hay datos para mostrar.")

        blocks = []
        for row in rows:
            blocks.append("\n".join(f"{k}: {v}" for k, v in row.items()))

        return {
            "type": "ir.actions.act_window",
            "name": "Preview RAW (estructura real)",
            "res_model": "saes.client.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_preview_text": "\n\n-----------------\n\n".join(blocks)
            },
        }
