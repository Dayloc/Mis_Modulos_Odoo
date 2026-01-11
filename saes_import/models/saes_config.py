from odoo import models, fields
from odoo.exceptions import UserError
from .saes_sqlserver import SaesSQLServerMixin
import psycopg2


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
            cur.execute(query)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
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
    # buscar opciones para provedores
    def action_choose_provider_table(self):
        self.ensure_one()

        tables = self.env["saes.detector"].detect_provider_tables(self)

        if not tables:
            raise UserError("No se detectaron tablas de proveedores.")

        # limpiar opciones anteriores
        self.env["saes.provider.table.option"].search([
            ("config_id", "=", self.id)
        ]).unlink()

        # crear opciones nuevas
        for t in tables:
            self.env["saes.provider.table.option"].create({
                "name": t,
                "config_id": self.id,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Elegir tabla de proveedores",
            "res_model": "saes.provider.table.selector",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
            },
        }


