from odoo.exceptions import UserError

class SaesClientImporter:
    def __init__(self, config):
        self.config = config
        self.env = config.env

    def import_clients(self, limit=None):
        """
        Importa clientes desde la tabla seleccionada
        """
        self._validate_config()
        rows = self._read_clients(limit=limit)

        for row in rows:
            try:
                self._import_single_client(row)
            except Exception as e:
                raise UserError(
                    f"Error importando cliente {row.get('code')}: {e}"
                )

    def _validate_config(self):
        if not self.config.client_table:
            raise UserError("No hay tabla de clientes seleccionada.")

    def _read_clients(self, limit=None):
        detector = self.env["saes.detector"]
        columns = detector.detect_client_columns(
            self.config, self.config.client_table
        )

        required = ["code", "name"]
        for r in required:
            if not columns.get(r):
                raise UserError(f"Falta columna obligatoria: {r}")

        sql_cols = []
        for key, col in columns.items():
            if col:
                if self.config.db_type == "postgres":
                    sql_cols.append(f'"{col}" AS {key}')
                else:
                    sql_cols.append(f'[{col}] AS {key}')

        limit_sql = ""
        if limit:
            if self.config.db_type == "postgres":
                limit_sql = f"LIMIT {limit}"
            else:
                limit_sql = f"TOP {limit}"

        if self.config.db_type == "postgres":
            query = f"""
                SELECT {', '.join(sql_cols)}
                FROM {self.config.client_table}
                {limit_sql}
            """
        else:
            query = f"""
                SELECT {limit_sql} {', '.join(sql_cols)}
                FROM {self.config.client_table}
            """

        return self.config._execute_sql(query)

    def _import_single_client(self, row):
        code = self.config._normalize_code(row.get("code"))
        name = row.get("name")

        if not code:
            raise UserError("Cliente sin código.")

        partner = self._find_existing_partner(code)

        vals = {
            "ref": code,
            "name": name or f"Cliente {code}",
            "email": row.get("email"),
            "street": row.get("street"),
            "zip": row.get("zip"),
            "city": row.get("city"),
            "is_company": True,
        }

        if partner:
            partner.write(vals)
        else:
            partner = self.env["res.partner"].create(vals)

        # aquí luego irá el External ID Map

    def _find_existing_partner(self, code):
        return self.env["res.partner"].search(
            [("ref", "=", code)],
            limit=1
        )
