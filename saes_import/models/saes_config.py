from odoo import models, fields
from odoo.exceptions import UserError
import psycopg2


class SaesImportConfig(models.Model):
    _name = "saes.import.config"
    _description = "Configuración Importador SAE"

    name = fields.Char(default="Configuración SAE")

    host = fields.Char(required=True)
    port = fields.Integer(default=5432)
    database = fields.Char(required=True)
    user = fields.Char(required=True)
    password = fields.Char(required=True)

    import_clientes = fields.Boolean(string="Importar clientes")
    import_direcciones = fields.Boolean(string="Importar direcciones")
    import_proveedores = fields.Boolean(string="Importar proveedores")


    def _get_saes_connection(self):
        try:
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password,
                connect_timeout=5,
            )
        except Exception as e:
            raise UserError(f"Error de conexión con SAE:\n{e}")

    def _table_exists(self, cur, table_name):
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = %s
            )
            """,
            (table_name,),
        )
        return cur.fetchone()[0]



    def action_test_connection(self):
        self.ensure_one()
        conn = self._get_saes_connection()
        conn.close()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Conexión exitosa",
                "message": "Conexión con SAE realizada correctamente.",
                "type": "success",
            },
        }



    def action_check_clients(self):
        self.ensure_one()

        if not self.import_clientes:
            raise UserError("La opción 'Importar clientes' no está activada.")

        conn = self._get_saes_connection()
        cur = conn.cursor()

        try:
            cur.execute("SELECT COUNT(*) FROM saes_clientes")
            total = cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Clientes detectados",
                "message": f"Se encontraron {total} clientes en SAE.",
                "type": "info",
            },
        }


    def action_preview_clients(self):
        self.ensure_one()

        if not self.import_clientes:
            raise UserError("La opción 'Importar clientes' no está activada.")

        conn = self._get_saes_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT cve_clie, nombre, email, telefono
                FROM saes_clientes
                ORDER BY fecha_alta
                LIMIT 5
                """
            )
            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        if not rows:
            raise UserError("No se encontraron clientes en SAE.")

        msg = ""
        for cve, nombre, email, telefono in rows:
            msg += f"- {nombre} | {email or 'sin email'} | {telefono or 'sin teléfono'}\n"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Preview clientes SAE",
                "message": msg,
                "type": "info",
                "sticky": True,
            },
        }



    def action_preview_addresses(self):
        self.ensure_one()

        if not self.import_direcciones:
            raise UserError("La opción 'Importar direcciones' no está activada.")

        conn = self._get_saes_connection()
        cur = conn.cursor()

        try:
            if self._table_exists(cur, "saes_direcciones"):
                cur.execute(
                    """
                    SELECT cve_clie, calle, ciudad, pais
                    FROM saes_direcciones
                    LIMIT 5
                    """
                )
                source = "saes_direcciones"
            else:
                cur.execute(
                    """
                    SELECT cve_clie, calle, ciudad, pais
                    FROM saes_clientes
                    WHERE calle IS NOT NULL
                    LIMIT 5
                    """
                )
                source = "saes_clientes"

            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        if not rows:
            raise UserError("No se encontraron direcciones en SAE.")

        msg = f"Fuente: {source}\n\n"
        for cve, calle, ciudad, pais in rows:
            msg += f"- Cliente {cve}: {calle}, {ciudad}, {pais}\n"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Preview direcciones SAE",
                "message": msg,
                "type": "info",
                "sticky": True,
            },
        }



    def action_import_clients(self):
        self.ensure_one()

        if not self.import_clientes:
            raise UserError("La opción 'Importar clientes' no está activada.")

        conn = self._get_saes_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT cve_clie, nombre, email, telefono
                FROM saes_clientes
                """
            )
            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        Partner = self.env["res.partner"].with_context(active_test=False)

        created = 0
        updated = 0

        for cve, nombre, email, telefono in rows:
            partner = Partner.search([("saes_code", "=", cve)], limit=1)

            vals = {
                "name": nombre,
                "email": email or False,
                "phone": telefono or False,
                "customer_rank": 1,
                "saes_code": cve,
            }

            if partner:
                partner.write(vals)
                updated += 1
            else:
                Partner.create(vals)
                created += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Importación completada",
                "message": (
                    f"Clientes creados: {created}\n"
                    f"Clientes actualizados: {updated}"
                ),
                "type": "success",
                "sticky": True,
            },
        }
