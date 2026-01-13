from odoo import models, fields
from odoo.exceptions import UserError


class SaleOrderTableSelector(models.TransientModel):
    _name = "sale.order.table.selector"
    _description = "Selector de tabla de pedidos"

    table_id = fields.Many2one(
        "sale.order.table.option",
        string="Tabla de pedidos",
        required=True,
        ondelete="cascade",
    )

    def action_confirm(self):
        self.ensure_one()

        active_id = self.env.context.get("active_id")
        if not active_id:
            raise UserError("No se encontró el contexto de configuración activa.")

        config = self.env["saes.import.config"].browse(active_id)
        if not config.exists():
            raise UserError("La configuración activa no existe.")

        # Guardar tabla seleccionada
        config.sale_order_table = self.table_id.name

        return {"type": "ir.actions.act_window_close"}

    def action_preview_sale_orders_raw(self):
        #raise UserError("DEBUG VERSION NUEVA SIN _execute_sql")
        #raise UserError("DEBUG: entro en preview sale orders")
        self.ensure_one()

        config = self.env["saes.import.config"].browse(
            self.env.context.get("active_id")
        )
        if not config.exists():
            raise UserError("No se encontró la configuración activa.")

        if not self.table_id:
            raise UserError("No hay tabla seleccionada.")

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
            "name": "Preview RAW pedidos (estructura real)",
            "res_model": "saes.client.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_preview_text": "\n\n-----------------\n\n".join(blocks)
            },
        }

