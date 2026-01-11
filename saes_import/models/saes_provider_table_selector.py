from odoo import models, fields
from odoo.exceptions import UserError


class SaesProviderTableSelector(models.TransientModel):
    _name = "saes.provider.table.selector"
    _description = "Selector de tabla de proveedores"

    table_id = fields.Many2one(
        "saes.provider.table.option",
        string="Tabla de proveedores",
        required=True,
    )

    def action_confirm(self):
        config = self.env["saes.import.config"].browse(
            self.env.context.get("active_id")
        )

        if not config:
            raise UserError("Configuración no encontrada.")

        config.provider_table = self.table_id.name

        return {"type": "ir.actions.act_window_close"}
