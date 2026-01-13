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

        config = self.env["saes.import.config"].browse(
            self.env.context.get("active_id")
        )
        if not config.exists():
            raise UserError("No hay configuración activa.")

        table = self.table_id.name

        conn = config._get_connection()
        try:
            cur = conn.cursor()

            if config.db_type == "postgres":
                query = f"SELECT * FROM {table} LIMIT 5"
                cur.execute(query)
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
                data = [dict(zip(cols, r)) for r in rows]

            else:
                # SQL Server SAFE MODE
                cur.execute(f"SELECT TOP 0 * FROM {table}")
                cols = [c[0] for c in cur.description]

                casted_cols = [
                    f"CAST([{c}] AS NVARCHAR(MAX)) AS [{c}]"
                    for c in cols
                ]

                query = f"""
                    SELECT TOP 5 {", ".join(casted_cols)}
                    FROM {table}
                """
                cur.execute(query)
                rows = cur.fetchall()
                data = [dict(zip(cols, r)) for r in rows]

        finally:
            conn.close()

        if not data:
            raise UserError("No hay datos para mostrar.")

        blocks = []
        for row in data:
            blocks.append(
                "\n".join(f"{k}: {v}" for k, v in row.items())
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Preview RAW Proveedores",
            "res_model": "saes.provider.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_preview_text": "\n\n-----------------\n\n".join(blocks)
            },
        }
