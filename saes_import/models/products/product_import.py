from odoo.exceptions import UserError


class SaesProductImporter:

    def __init__(self, config):
        self.config = config
        self.env = config.env

    # ---------------------------------------------------------
    # PUBLIC
    # ---------------------------------------------------------

    def import_products(self, limit=None):
        self._validate_config()
        rows = self._read_products(limit)

        for row in rows:
            try:
                self._import_single_product(row)
            except Exception as e:
                raise UserError(
                    f"Error importando producto {row.get('code')}: {e}"
                )

    # ---------------------------------------------------------
    # VALIDACIONES
    # ---------------------------------------------------------

    def _validate_config(self):
        if not self.config.product_table:
            raise UserError("No hay tabla de productos seleccionada.")

    # ---------------------------------------------------------
    # LECTURA SQL
    # ---------------------------------------------------------

    def _read_products(self, limit=None):
        detector = self.env["saes.detector"]
        columns = detector.detect_product_columns(
            self.config, self.config.product_table
        )

        if not columns.get("code") or not columns.get("name"):
            raise UserError("Producto sin columnas obligatorias (code / name).")

        sql_cols = []

        for key, col in columns.items():
            if not col:
                continue

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
                FROM {self.config.product_table}
                {limit_sql}
            """
        else:
            query = f"""
                SELECT {limit_sql} {', '.join(sql_cols)}
                FROM {self.config.product_table}
            """

        return self.config._execute_sql(query)

    # ---------------------------------------------------------
    # IMPORTACIÓN INDIVIDUAL
    # ---------------------------------------------------------


    def _import_single_product(self, row):

            code = self._clean(row.get("code"))
            name = self._clean(row.get("name"))
            name2 = self._clean(row.get("name2"))

            if not code:
                raise UserError(_("Producto sin código."))

            product = self._find_existing_product(code)

            full_name = (
                f"{name} - {name2}"
                if name and name2
                else name or f"Producto {code}"
            )

            # ---------- DESCRIPCIÓN ----------
            description = self._clean(row.get("description"))

            # ---------- PRECIOS ----------
            price = self._to_float(row.get("price"))
            cost = self._to_float(row.get("cost"))

            # ---------- ESTADO ----------
            active = True
            baja = row.get("active")
            if baja in (1, "1", True):
                active = False

            # ---------- PESO / VOLUMEN ----------
            weight = self._to_float(row.get("weight"))
            volume = self._to_float(row.get("volume"))

            # ---------- VALORES ----------
            # ⚠️ NO PASAR type NI detailed_type EN ODOO 18
            vals = {
                "default_code": code,
                "name": full_name,
                "active": active,
                "description": description or False,
                "list_price": price or 0.0,
                "standard_price": cost or 0.0,
                "weight": weight or 0.0,
                "volume": volume or 0.0,
            }

            if product:
                product.write(vals)
            else:
                self.env["product.template"].create(vals)

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _find_existing_product(self, code):
        return self.env["product.template"].search(
            [("default_code", "=", code)],
            limit=1
        )

    def _clean(self, value):
        if not value:
            return None
        return str(value).strip()

    def _to_float(self, value):
        try:
            return float(value)
        except Exception:
            return None
