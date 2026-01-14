from odoo import models, fields
from odoo.exceptions import UserError


class SaesTableSelector(models.TransientModel):
    _name = "saes.table.selector"
    _description = "Selector de tabla de clientes"

    table_id = fields.Many2one(
        "saes.client.table.option",
        string="Tabla de clientes",
        required=True,
        ondelete="cascade",
    )
    preview_text = fields.Text(
        string="Preview",
        readonly=True
    )

    def action_confirm(self):
        self.ensure_one()

        config = self.env["saes.import.config"].browse(
            self.env.context.get("active_id")
        )

        if not config.exists():
            raise UserError("No se encontró la configuración activa.")

        config.client_table = self.table_id.name

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
        finally:
            conn.close()

        if not rows:
            raise UserError("No hay datos para mostrar.")

        # solo primeras 6 columnas
        preview_cols = cols[:10]

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view">
                <thead class="table-info">
                    <tr>
        """

        for col in preview_cols:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for row in rows:
            row_dict = dict(zip(cols, row))
            html += "<tr>"
            for col in preview_cols:
                val = row_dict.get(col)
                html += f"<td>{val if val is not None else ''}</td>"
            html += "</tr>"

        html += """
                </tbody>
            </table>
        </div>
        """

        return {
            "type": "ir.actions.act_window",
            "name": f"Preview RAW ({table})",
            "res_model": "saes.client.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html,
            },
        }


