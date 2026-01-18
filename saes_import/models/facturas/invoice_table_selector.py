from odoo import models, fields
from odoo.exceptions import UserError


class SaesInvoiceTableSelector(models.TransientModel):
    _name = "saes.invoice.table.selector"
    _description = "Selector de tabla de facturas"

    table_id = fields.Many2one(
        "saes.invoice.table.option",
        string="Tabla de facturas",
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
            raise UserError("No hay configuración activa.")

        invoice_type = self.env.context.get("invoice_type")

        if invoice_type == "sale":
            config.sale_invoice_table = self.table_id.name
        elif invoice_type == "purchase":
            config.purchase_invoice_table = self.table_id.name
        else:
            raise UserError("Tipo de factura no definido.")

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
                query = f'SELECT * FROM "{table}" LIMIT 5'
                cur.execute(query)
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
            else:
                cur.execute(f"SELECT TOP 0 * FROM [{table}]")
                cols = [c[0] for c in cur.description]

                casted_cols = [
                    f"CAST([{c}] AS NVARCHAR(MAX)) AS [{c}]"
                    for c in cols
                ]

                query = f"""
                    SELECT TOP 5 {", ".join(casted_cols)}
                    FROM [{table}]
                """
                cur.execute(query)
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            raise UserError("No hay datos para mostrar.")

        preview_cols = cols[:10]

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view">
                <thead class="table-info">
                    <tr>
                        <th class="text-center">#</th>
        """

        for col in preview_cols:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for idx, row in enumerate(rows, start=1):
            row_dict = dict(zip(cols, row))
            html += "<tr>"
            html += f"<td style='text-align:center; font-weight:600;'>{idx}</td>"
            for col in preview_cols:
                html += f"<td>{row_dict.get(col) or ''}</td>"
            html += "</tr>"

        html += """
                </tbody>
            </table>
        </div>
        """

        return {
            "type": "ir.actions.act_window",
            "name": f"Preview RAW ({table})",
            "res_model": "saes.invoice.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html,
            },
        }
