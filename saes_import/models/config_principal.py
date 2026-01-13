from odoo import models, fields
from odoo.exceptions import UserError
from .sqlserver_configuration import SaesSQLServerMixin
import psycopg2
import pandas as pd




class SaesImportConfig(models.Model, SaesSQLServerMixin):
    _name = "saes.import.config"
    _description = "Configuración Importador SAE"

    name = fields.Char(default="Configuración SAE")

    host = fields.Char(required=True)
    port = fields.Integer(default=5432)
    database = fields.Char(required=True)
    user = fields.Char(required=True)
    password = fields.Char(required=True)

    import_clientes = fields.Boolean()
    import_direcciones = fields.Boolean()
    import_proveedores = fields.Boolean()

    db_type = fields.Selection(
        [("postgres", "PostgreSQL"), ("sqlserver", "SQL Server")],
        default="postgres",
        required=True,
    )

    client_table = fields.Char(readonly=True)
    provider_table = fields.Char(readonly=True)
    product_table = fields.Char(readonly=True)
    sale_order_table = fields.Char(readonly=True)

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
        if not isinstance(query, str):
            raise UserError(f"Query inválida: {type(query)}")

        conn = self._get_connection()

        # 🔥 SQL SERVER → pandas
        if self.db_type == "sqlserver":
            df = pd.read_sql(query, conn)
            return df.to_dict(orient="records")

        # PostgreSQL normal
        try:
            cursor = conn.cursor()
            cursor.execute(query)

            description = cursor.description
            if not description:
                return []

            columns = [col[0] for col in description]

            rows = []
            for row in cursor:
                rows.append(dict(zip(columns, row)))

            return rows
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
        Option.search([]).unlink()  # limpiamos anteriores

        for t in tables:
            Option.create({"name": t})

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
    def _preview_clients(self, limit=5):
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

        rows = self._preview_clients(limit=5)
        if not rows:
            raise UserError("No hay datos para mostrar.")

        text = []
        for r in rows:
            text.append(
                        f"""Cliente: {r.get('name', '—')}
        Código: {r.get('code', '—')}
        Email: {r.get('email', '—')}
        Dirección: {r.get('street', '—')}
        CP / Ciudad: {r.get('zip', '—')} {r.get('city', '—')}
        """
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Preview clientes",
            "res_model": "saes.client.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_preview_text": "\n-----------------\n".join(text)
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
    def _preview_providers(self, limit=5):
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

        rows = self._preview_providers(limit=5)

        if not rows:
            raise UserError("No hay datos para mostrar.")

        text = []
        for r in rows:
            text.append(
                f"""Proveedor: {r.get('name', '—')}
    Código: {r.get('code', '—')}
    Email: {r.get('email', '—')}
    """
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Preview proveedores",
            "res_model": "saes.client.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_preview_text": "\n-----------------\n".join(text)
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
    def _preview_products(self, limit=5):
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

        rows = self._preview_products(limit=5)

        if not rows:
            raise UserError("No hay datos para mostrar.")

        text = []
        for r in rows:
            text.append(
                f"""Producto: {r.get('name', '—')}
    Código: {r.get('code', '—')}
    Tipo: {r.get('type', '—')}
    """
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Preview productos",
            "res_model": "saes.client.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_preview_text": "\n-----------------\n".join(text)
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
    #acción detectar tablas pedidos
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

            # escape según motor
            if self.db_type == "postgres":
                sql_col = f'"{col}"'
            else:
                sql_col = f'[{col}]'

            sql_cols.append(f"{sql_col} AS {key}")

        if not sql_cols:
            raise UserError("No se detectaron columnas válidas para preview.")

        if self.db_type == "postgres":
            query = f"""
                SELECT {', '.join(sql_cols)}
                FROM {self.sale_order_table}
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT TOP {limit} {', '.join(sql_cols)}
                FROM {self.sale_order_table}
            """

        return self._execute_sql(query)

    def action_preview_sale_orders(self):
        self.ensure_one()

        if not self.sale_order_table:
            raise UserError("No hay tabla de pedidos seleccionada.")

        rows = self._preview_sale_orders(limit=5)

        if not rows:
            raise UserError("No hay datos para mostrar.")

        blocks = []
        for r in rows:
            blocks.append(
                f"""Pedido: {r.get('number') or '—'}
    Fecha: {r.get('date') or '—'}
    Cliente: {r.get('customer') or '—'}
    Total: {r.get('total') or '—'}
    Estado: {r.get('state') or '—'}"""
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Preview pedidos",
            "res_model": "saes.client.preview.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_preview_text": "\n-----------------\n".join(blocks)
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

