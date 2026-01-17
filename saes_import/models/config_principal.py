from odoo import models, fields
from odoo.exceptions import UserError
from .sqlserver_configuration import SaesSQLServerMixin
import psycopg2




class SaesImportConfig(models.Model, SaesSQLServerMixin):
    _name = "saes.import.config"
    _description = "Configuración Importador SAGE"

    name = fields.Char(default="Configuración SAGE")

    host = fields.Char(required=True)
    port = fields.Integer(default=5432)
    database = fields.Char(required=True)
    user = fields.Char(required=True)
    password = fields.Char(required=True)

    import_clientes = fields.Boolean()
    import_direcciones = fields.Boolean()
    import_proveedores = fields.Boolean()
    import_pedidos = fields.Boolean()
    import_productos = fields.Boolean()
    import_sale_order_lines = fields.Boolean()
    import_invoices = fields.Boolean()

    db_type = fields.Selection(
        [("postgres", "PostgreSQL"), ("sqlserver", "SQL Server")],
        default="postgres",
        required=True,
    )

    client_table = fields.Char(readonly=True)
    provider_table = fields.Char(readonly=True)
    product_table = fields.Char(readonly=True)
    sale_order_table = fields.Char(readonly=True)
    sale_order_line_table = fields.Char(readonly=True)
    invoice_table = fields.Char(readonly=True)

    # conexión para ambos sql sever/ posgres


    def _get_connection(self):
        if self.db_type == "postgres":
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password,
            )
        return self._get_sqlserver_connection()

    def _execute_sql(self, query):
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if self.db_type == "sqlserver":
                # 1️⃣ Obtener columnas
                cur.execute(f"SELECT TOP 0 * FROM ({query}) t")
                cols = [c[0] for c in cur.description]

                # 2️⃣ CASTEAR TODO A NVARCHAR
                casted_cols = [
                    f"CAST([{c}] AS NVARCHAR(MAX)) AS [{c}]"
                    for c in cols
                ]

                safe_query = f"""
                    SELECT {", ".join(casted_cols)}
                    FROM ({query}) t
                """

                cur.execute(safe_query)
            else:
                cur.execute(query)

            cols = [c[0] for c in cur.description]
            rows = cur.fetchall()

            return [dict(zip(cols, row)) for row in rows]

        finally:
            conn.close()

    # detectar tablas

    def action_detect_tables(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_tables(self)

        wizard = self.env["saes.detected.tables.wizard"].create({})

        for t in tables:
            self.env["saes.detected.table"].create({
                "name": t,
                "wizard_id": wizard.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Tablas detectadas",
            "res_model": "saes.detected.tables.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    # seleccionar tablas
    def action_choose_client_table(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_client_tables(self)
        if not tables:
            raise UserError("No se detectaron tablas candidatas a clientes.")

        Option = self.env["saes.client.table.option"]
        Option.search([]).unlink()  # 🔥 solo clientes

        for t in tables:
            Option.create({
                "name": t,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Elegir tabla de clientes",
            "res_model": "saes.table.selector",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
            },
        }

    def action_detect_client_tables(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_client_tables(self)

        wizard = self.env["saes.detected.tables.wizard"].create({})

        for t in tables:
            self.env["saes.detected.table"].create({
                "name": t,
                "wizard_id": wizard.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Tablas candidatas a clientes",
            "res_model": "saes.detected.tables.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    # preview de clientes-solo lectura
    def _preview_clients(self, limit=8):
        self.ensure_one()

        if not self.client_table:
            raise UserError("No hay tabla de clientes seleccionada.")

        detector = self.env["saes.detector"]
        columns = detector.detect_client_columns(self, self.client_table)

        if not columns:
            raise UserError("No se pudieron detectar columnas de clientes.")

        sql_cols = []
        for key, col in columns.items():
            if col:
                col = str(col)
                sql_cols.append(f"{col} AS {key}")

        if not sql_cols:
            raise UserError("No hay columnas válidas para preview.")

        if self.db_type == "postgres":
            query = f"""
                SELECT {', '.join(sql_cols)}
                FROM {self.client_table}
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT TOP {limit} {', '.join(sql_cols)}
                FROM {self.client_table}
            """

        return self._execute_sql(query)

    def action_preview_clients(self):
        self.ensure_one()

        rows = self._preview_clients(limit=15)
        if not rows:
            raise UserError("No hay datos para mostrar.")

        # columnas dinámicas (NO hardcodeadas)
        columns = list(rows[0].keys())

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view">
                <thead class="table-info">
                    <tr>
                        <th class="text-center">#</th>
        """

        for col in columns:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for idx, row in enumerate(rows, start=1):
            html += "<tr>"
            html += f"<td style='text-align:center; font-weight:600;'>{idx}</td>"
            for col in columns:
                html += f"<td>{row.get(col) or ''}</td>"
            html += "</tr>"

        html += """
                </tbody>
            </table>
        </div>
        """

        return {
            "type": "ir.actions.act_window",
            "name": "Preview clientes",
            "res_model": "saes.client.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html
            },
        }

    # notificaciones
    def _notify(self, title, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message or "—",
                "type": "info",
                "sticky": True,
            },
        }
    # candidatas a tablas de provedores
    def action_detect_provider_tables(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_provider_tables(self)

        if not tables:
            raise UserError("No se detectaron tablas candidatas a proveedores.")

        wizard = self.env["saes.detected.tables.wizard"].create({})

        for t in tables:
            self.env["saes.detected.table"].create({
                "name": t,
                "wizard_id": wizard.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Tablas candidatas a proveedores",
            "res_model": "saes.detected.tables.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    # buscar opciones para provedores
    def action_choose_provider_table(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_provider_tables(self)

        if not tables:
            raise UserError("No se detectaron tablas de proveedores.")

        Option = self.env["saes.provider.table.option"]

        for t in tables:
            if not Option.search([
                ("name", "=", t),
                ("config_id", "=", self.id),
            ], limit=1):
                Option.create({
                    "name": t,
                    "config_id": self.id,
                })

        return {
            "type": "ir.actions.act_window",
            "name": "Elegir tabla de proveedores",
            "res_model": "saes.provider.table.selector",
            "view_mode": "form",
            "views": [
                (self.env.ref(
                    "saes_import.view_saes_provider_table_selector_form"
                ).id, "form")
            ],
            "target": "new",
            "context": {
                "active_id": self.id,
            },
        }

    # previo de provedores
    def _preview_providers(self, limit=8):
        self.ensure_one()

        if not self.provider_table:
            raise UserError("No hay tabla de proveedores seleccionada.")

        detector = self.env["saes.detector"]
        columns = detector.detect_provider_columns(self, self.provider_table)

        if not columns:
            raise UserError("No se pudieron detectar columnas de proveedores.")

        sql_cols = []
        for key, col in columns.items():
            if col:
                sql_cols.append(f"{col} AS {key}")

        if not sql_cols:
            raise UserError("No hay columnas válidas para preview.")

        if self.db_type == "postgres":
            query = f"""
                SELECT {', '.join(sql_cols)}
                FROM {self.provider_table}
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT TOP {limit} {', '.join(sql_cols)}
                FROM {self.provider_table}
            """

        return self._execute_sql(query)

    def action_preview_providers(self):
        self.ensure_one()

        rows = self._preview_providers(limit=15)
        if not rows:
            raise UserError("No hay datos para mostrar.")

        columns = list(rows[0].keys())

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view">
                <thead class="table-primary">
                    <tr>
                        <th 
                        class="text-center">#</th>
        """

        for col in columns:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for idx, row in enumerate(rows, start=1):
            html += "<tr>"
            html += f"<td style='text-align:center; font-weight:600;'>{idx}</td>"
            for col in columns:
                html += f"<td>{row.get(col) or ''}</td>"
            html += "</tr>"

        html += """
                </tbody>
            </table>
        </div>
        """

        return {
            "type": "ir.actions.act_window",
            "name": "Preview proveedores",
            "res_model": "saes.provider.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html
            },
        }

    # acción para abrir selector de productos
    def action_choose_product_table(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_product_tables(self)

        if not tables:
            raise UserError("No se detectaron tablas de productos.")

        Option = self.env["product.table.option"]

        for t in tables:
            if not Option.search([
                ("name", "=", t),
                ("config_id", "=", self.id),
            ], limit=1):
                Option.create({
                    "name": t,
                    "config_id": self.id,
                })

        return {
            "type": "ir.actions.act_window",
            "name": "Elegir tabla de productos",
            "res_model": "product.table.selector",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
            },
        }
    # acción para el método previo de producto
    def _preview_products(self, limit=8):
        self.ensure_one()

        if not self.product_table:
            raise UserError("No hay tabla de productos seleccionada.")

        detector = self.env["saes.detector"]
        columns = detector.detect_product_columns(self, self.product_table)

        if not columns:
            raise UserError("No se pudieron detectar columnas de productos.")

        sql_cols = []
        for key, col in columns.items():
            if col:
                sql_cols.append(f"{col} AS {key}")

        if not sql_cols:
            raise UserError("No hay columnas válidas para preview.")

        if self.db_type == "postgres":
            query = f"""
                SELECT {', '.join(sql_cols)}
                FROM {self.product_table}
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT TOP {limit} {', '.join(sql_cols)}
                FROM {self.product_table}
            """

        return self._execute_sql(query)

    # acción para el preview de productos
    def action_preview_products(self):
        self.ensure_one()

        rows = self._preview_products(limit=15)
        if not rows:
            raise UserError("No hay datos para mostrar.")

        columns = list(rows[0].keys())

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view">
                <thead class="table-primary">
                    <tr>
                        <th class="text-center">#</th>
        """

        for col in columns:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for idx, row in enumerate(rows, start=1):
            html += "<tr>"
            html += f"<td style='text-align:center; font-weight:600;'>{idx}</td>"
            for col in columns:
                val = row.get(col)
                html += f"<td>{val if val is not None else ''}</td>"
            html += "</tr>"

        html += """
                </tbody>
            </table>
        </div>
        """

        return {
            "type": "ir.actions.act_window",
            "name": "Preview productos",
            "res_model": "product.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html
            },
        }

    #tablas candidatas de productos
    def action_detect_product_tables(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_product_tables(self)

        if not tables:
            raise UserError("No se detectaron tablas candidatas de productos.")

        wizard = self.env["saes.detected.tables.wizard"].create({})

        for t in tables:
            self.env["saes.detected.table"].create({
                "name": t,
                "wizard_id": wizard.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Tablas candidatas de productos",
            "res_model": "saes.detected.tables.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }
    #acción detectar tablas pedid
    def action_detect_sale_order_tables(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_sale_order_tables(self)

        if not tables:
            raise UserError("No se detectaron tablas candidatas a pedidos.")

        wizard = self.env["saes.detected.tables.wizard"].create({})

        for t in tables:
            self.env["saes.detected.table"].create({
                "name": t,
                "wizard_id": wizard.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Tablas candidatas a pedidos",
            "res_model": "saes.detected.tables.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    def action_choose_sale_order_table(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_sale_order_tables(self)
        if not tables:
            raise UserError("No se detectaron tablas de pedidos.")

        Option = self.env["sale.order.table.option"]
        Option.search([
            ("config_id", "=", self.id)
        ]).unlink()

        for t in tables:
            Option.create({
                "name": t,
                "config_id": self.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Elegir tabla de pedidos",
            "res_model": "sale.order.table.selector",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
            },
        }

    def action_preview_sale_orders(self):
        self.ensure_one()

        if not self.sale_order_table:
            raise UserError("No hay tabla de pedidos seleccionada.")

        rows = self._preview_sale_orders(limit=5)
        if not rows:
            raise UserError("No hay datos para mostrar.")

        columns = list(rows[0].keys())

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view">
                <thead class="table-primary">
                    <tr>
                        <th>#</th>
        """

        for col in columns:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for idx, row in enumerate(rows, start=1):
            html += "<tr>"
            html += f"<td style='text-align:center; font-weight:600;'>{idx}</td>"
            for col in columns:
                val = row.get(col)
                html += f"<td>{val if val is not None else ''}</td>"
            html += "</tr>"

        html += """
                </tbody>
            </table>
        </div>
        """

        return {
            "type": "ir.actions.act_window",
            "name": "Preview pedidos",
            "res_model": "saes.sale.order.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html
            },
        }

    def _preview_sale_orders(self, limit=5):
        self.ensure_one()

        if not self.sale_order_table:
            raise UserError("No hay tabla de pedidos seleccionada.")

        detector = self.env["saes.detector"]
        columns = detector.detect_sale_order_columns(
            self, self.sale_order_table
        )

        sql_cols = []
        for key, col in columns.items():
            if not col:
                continue

            if self.db_type == "postgres":
                sql_col = f'"{col}"'
            else:
                sql_col = f'[{col}]'

            sql_cols.append(f"{sql_col} AS {key}")

        if not sql_cols:
            raise UserError("No se detectaron columnas válidas para preview.")

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if self.db_type == "postgres":
                query = f"""
                    SELECT {', '.join(sql_cols)}
                    FROM {self.sale_order_table}
                    LIMIT {limit}
                """
                cur.execute(query)
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()

            else:
                # SQL Server SAFE MODE
                cur.execute(f"SELECT TOP 0 {', '.join(sql_cols)} FROM {self.sale_order_table}")
                cols = [c[0] for c in cur.description]

                casted_cols = [
                    f"CAST({c.split(' AS ')[0]} AS NVARCHAR(MAX)) AS {c.split(' AS ')[1]}"
                    for c in sql_cols
                ]

                query = f"""
                    SELECT TOP {limit} {', '.join(casted_cols)}
                    FROM {self.sale_order_table}
                """
                cur.execute(query)
                rows = cur.fetchall()

            return [dict(zip(cols, r)) for r in rows]

        finally:
            conn.close()

    def preview_raw_table(self, table, limit=5):
        self.ensure_one()

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if self.db_type == "postgres":
                query = f"""
                    SELECT *
                    FROM {table}
                    LIMIT {limit}
                """
                cur.execute(query)
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()

            else:
                # SQL Server SAFE MODE
                cur.execute(f"SELECT TOP 0 * FROM {table}")
                cols = [c[0] for c in cur.description]

                casted_cols = [
                    f"CAST([{c}] AS NVARCHAR(MAX)) AS [{c}]"
                    for c in cols
                ]

                query = f"""
                    SELECT TOP {limit} {", ".join(casted_cols)}
                    FROM {table}
                """
                cur.execute(query)
                rows = cur.fetchall()

            return [dict(zip(cols, r)) for r in rows]

        finally:
            conn.close()

        # boton de importación de  prueba temporal
    def action_import_all_clients(self):
            self.ensure_one()

            from .client.clients_import import SaesClientImporter

            importer = SaesClientImporter(self)
            importer.import_clients()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Importación",
                    "message": "Clientes importados correctamente",
                    "type": "success",
                    "sticky": False,
                },
            }

    def _normalize_code(self, value):
         return value.strip().upper() if value else None

    #boton de importar proveedores
    def action_import_all_providers(self):
        self.ensure_one()

        from .provider.providers_import import SaesProviderImporter

        importer = SaesProviderImporter(self)
        importer.import_providers()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Importación",
                "message": "Proveedores importados correctamente",
                "type": "success",
                "sticky": False,
            },
        }

    # importador de productos
    def action_import_products(self):
        self.ensure_one()
        from .products.product_import import SaesProductImporter

        importer = SaesProductImporter(self)
        importer.import_products()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Importación",
                "message": "Productos importados correctamente",
                "type": "success",
            },
        }

    # metodo para detectar tablas de líneas
    def action_detect_sale_order_line_tables(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_sale_order_line_tables(self)

        if not tables:
            raise UserError("No se detectaron tablas candidatas a líneas de pedido.")

        wizard = self.env["saes.detected.tables.wizard"].create({})

        for t in tables:
            self.env["saes.detected.table"].create({
                "name": t,
                "wizard_id": wizard.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Tablas candidatas a líneas de pedido",
            "res_model": "saes.detected.tables.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    def action_choose_sale_order_line_table(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_sale_order_line_tables(self)
        if not tables:
            raise UserError("No se detectaron tablas de líneas de pedido.")

        Option = self.env["sale.order.line.table.option"]

        Option.search([
            ("config_id", "=", self.id)
        ]).unlink()

        for t in tables:
            Option.create({
                "name": t,
                "config_id": self.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Elegir tabla de líneas de pedido",
            "res_model": "sale.order.line.table.selector",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
            },
        }

    def action_preview_sale_order_lines(self):
        self.ensure_one()

        rows = self._preview_sale_order_lines(limit=15)
        if not rows:
            raise UserError("No hay datos para mostrar.")

        columns = list(rows[0].keys())

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view">
                <thead class="table-info">
                    <tr>
                        <th class="text-center">#</th>
        """

        for col in columns:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for idx, row in enumerate(rows, start=1):
            html += "<tr>"
            html += f"<td style='text-align:center; font-weight:600;'>{idx}</td>"
            for col in columns:
                html += f"<td>{row.get(col) or ''}</td>"
            html += "</tr>"

        html += "</tbody></table></div>"

        return {
            "type": "ir.actions.act_window",
            "name": "Preview líneas de pedido",
            "res_model": "saes.sale.order.line.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html,
            },
        }

    def _preview_sale_order_lines(self, limit=15):
        self.ensure_one()

        if not self.sale_order_line_table:
            raise UserError("No hay tabla de líneas seleccionada.")

        if self.db_type == "postgres":
            query = f"""
                SELECT *
                FROM {self.sale_order_line_table}
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT TOP {limit} *
                FROM {self.sale_order_line_table}
            """

        return self._execute_sql(query)

    # invoice (facturas)
    def action_detect_invoice_tables(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_invoice_tables(self)
        if not tables:
            raise UserError("No se detectaron tablas de facturas.")

        wizard = self.env["saes.detected.tables.wizard"].create({})

        for t in tables:
            self.env["saes.detected.table"].create({
                "name": t,
                "wizard_id": wizard.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Tablas candidatas a facturas",
            "res_model": "saes.detected.tables.wizard",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    def action_choose_invoice_table(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_invoice_tables(self)
        if not tables:
            raise UserError("No se detectaron tablas de facturas.")

        Option = self.env["saes.invoice.table.option"]
        Option.search([("config_id", "=", self.id)]).unlink()

        for t in tables:
            Option.create({
                "name": t,
                "config_id": self.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Elegir tabla de facturas",
            "res_model": "saes.invoice.table.selector",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
            },
        }

    def _preview_invoices(self, limit=10):
        self.ensure_one()

        if not self.invoice_table:
            raise UserError("No hay tabla de facturas seleccionada.")

        detector = self.env["saes.detector"]
        columns = detector.detect_invoice_columns(self, self.invoice_table)

        sql_cols = []
        for key, col in columns.items():
            if not col:
                continue

            if self.db_type == "postgres":
                sql_cols.append(f'"{col}" AS {key}')
            else:
                sql_cols.append(f'[{col}] AS {key}')

        if not sql_cols:
            raise UserError("No se detectaron columnas válidas de facturas.")

        if self.db_type == "postgres":
            query = f"""
                SELECT {', '.join(sql_cols)}
                FROM {self.invoice_table}
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT TOP {limit} {', '.join(sql_cols)}
                FROM {self.invoice_table}
            """

        return self._execute_sql(query)

    def action_preview_invoices(self):
        self.ensure_one()

        rows = self._preview_invoices(limit=15)
        if not rows:
            raise UserError("No hay datos para mostrar.")

        # columnas dinámicas
        columns = list(rows[0].keys())

        html = """
        <div style="overflow-x:auto; max-width:100%;">
            <table class="table table-sm table-bordered o_list_view">
                <thead class="table-primary">
                    <tr>
                        <th style="width:40px; text-align:center;">#</th>
        """

        for col in columns:
            html += f"<th>{col.upper()}</th>"

        html += "</tr></thead><tbody>"

        for idx, row in enumerate(rows, start=1):
            html += "<tr>"
            html += (
                "<td style='width:40px; text-align:center; font-weight:600;'>"
                f"{idx}</td>"
            )
            for col in columns:
                html += f"<td>{row.get(col) or ''}</td>"
            html += "</tr>"

        html += """
                </tbody>
            </table>
        </div>
        """

        return {
            "type": "ir.actions.act_window",
            "name": "Preview facturas",
            "res_model": "saes.invoice.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "preview_html": html
            },
        }

















