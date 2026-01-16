from odoo import models, fields,api

class SaesDetectedTablesWizard(models.TransientModel):
    _name = "saes.detected.tables.wizard"
    _description = "Tablas detectadas"

    table_ids = fields.One2many(
        "saes.detected.table",
        "wizard_id",
        string="Tablas"
    )
    selected_table_id = fields.Many2one(
        "saes.detected.table",
        string="Tabla",
        ondelete="cascade",
    )

    preview_html = fields.Html(
        string="Preview",
        readonly=True,
    )

    @api.onchange("selected_table_id")
    def _onchange_table_id_preview(self):
        self.preview_html = False

        if not self.selected_table_id:
            return

        config = self.env["saes.import.config"].browse(
            self.env.context.get("active_id")
        )
        if not config.exists():
            self.preview_html = "<p>No hay configuración activa.</p>"
            return

        table = self.selected_table_id.name

        try:
            conn = config._get_connection()
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
            self.preview_html = "<p>No hay datos para mostrar.</p>"
            return

        preview_cols = cols[:10]

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view" style="table-layout: fixed; width: 100%;">
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

        self.preview_html = html

