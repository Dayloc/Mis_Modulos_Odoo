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

    def action_preview_raw(self):
        self.ensure_one()

        active_id = self.env.context.get("active_id")
        if not active_id:
            raise UserError("No hay configuración activa.")

        config = self.env["saes.import.config"].browse(active_id)
        if not config.exists():
            raise UserError("La configuración no existe.")

        rows = config.preview_raw_table(self.table_id.name, limit=5)

        if not rows:
            raise UserError("No hay datos para mostrar.")

        blocks = []
        for row in rows:
            blocks.append(
                "\n".join(f"{k}: {v}" for k, v in row.items())
            )

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
