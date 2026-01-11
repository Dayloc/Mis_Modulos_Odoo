from odoo import models, fields
from odoo.exceptions import UserError


class SaesProviderTableSelector(models.TransientModel):
    _name = "saes.provider.table.selector"
    _description = "Selector de tabla de proveedores"

    table_id = fields.Many2one(
        "saes.provider.table.option",
        string="Tabla de proveedores",
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

        config.provider_table = self.table_id.name

        return {"type": "ir.actions.act_window_close"}

