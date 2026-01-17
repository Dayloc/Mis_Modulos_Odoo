from odoo import models, fields
from odoo.exceptions import UserError


class SaleOrderLineTableOption(models.TransientModel):
    _name = "sale.order.line.table.option"
    _description = "Tabla candidata de líneas de pedido"

    name = fields.Char(string="Tabla", required=True)
    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade"
    )


class SaleOrderLineTableSelector(models.TransientModel):
    _name = "sale.order.line.table.selector"
    _description = "Selector de tabla de líneas de pedido"

    table_id = fields.Many2one(
        "sale.order.line.table.option",
        string="Tabla de líneas",
        required=True,
        ondelete="cascade",
    )

    def action_confirm(self):
        self.ensure_one()

        config = self.env["saes.import.config"].browse(
            self.env.context.get("active_id")
        )
        if not config.exists():
            raise UserError("No hay configuración activa.")

        config.sale_order_line_table = self.table_id.name

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
                cur.execute(f'SELECT * FROM "{table}" LIMIT 15')
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
            else:
                cur.execute(f"SELECT TOP 0 * FROM [{table}]")
                cols = [c[0] for c in cur.description]

                casted_cols = [
                    f"CAST([{c}] AS NVARCHAR(MAX)) AS [{c}]"
                    for c in cols
                ]

                cur.execute(f"""
                    SELECT TOP 15 {", ".join(casted_cols)}
                    FROM [{table}]
                """)
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            raise UserError("No hay datos para mostrar.")

        preview_cols = cols[:10]

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view"
                   style="table-layout:fixed; width:100%;">
                <thead class="table-info">
                    <tr>
                        <th style="width:40px; text-align:center;">#</th>
        """

        for col in preview_cols:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for idx, row in enumerate(rows, start=1):
            row_dict = dict(zip(cols, row))
            html += "<tr>"
            html += f'<td style="width:40px; text-align:center; font-weight:600;">{idx}</td>'
            for col in preview_cols:
                html += f"<td>{row_dict.get(col) or ''}</td>"
            html += "</tr>"

        html += "</tbody></table></div>"

        return {
            "type": "ir.actions.act_window",
            "name": f"Preview RAW líneas ({table})",
            "res_model": "saes.sale.order.line.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html,
            },
        }
