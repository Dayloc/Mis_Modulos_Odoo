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
            limit_sql = (
                f"LIMIT {limit}"
                if self.config.db_type == "postgres"
                else f"TOP {limit}"
            )

        query = (
            f"SELECT {', '.join(sql_cols)} FROM {self.config.product_table} {limit_sql}"
            if self.config.db_type == "postgres"
            else f"SELECT {limit_sql} {', '.join(sql_cols)} FROM {self.config.product_table}"
        )

        return self.config._execute_sql(query)

    # ---------------------------------------------------------
    # IMPORTACIÓN INDIVIDUAL
    # ---------------------------------------------------------

    def _import_single_product(self, row):

        # ---------- DATOS BÁSICOS ----------
        code = self._clean(row.get("code"))
        name = self._clean(row.get("name"))
        name2 = self._clean(row.get("name2"))

        if not code:
            raise UserError("Producto sin código.")

        template = self._find_existing_product(code)

        full_name = (
            f"{name} - {name2}"
            if name and name2
            else name or f"Producto {code}"
        )

        # campos
        description = self._clean(row.get("description"))
        price = self._to_float(row.get("price"))
        cost = self._to_float(row.get("cost"))
        weight = self._to_float(row.get("weight"))
        volume = self._to_float(row.get("volume"))
        stock_qty = self._to_float(row.get("stock"))

        active = True
        if row.get("active") in (1, "1", True):
            active = False

        # inventario
        is_storable = stock_qty is not None

        vals = {
            "default_code": code,
            "name": full_name,
            "active": active,
            "description": description or False,
            "list_price": price or 0.0,
            "standard_price": cost or 0.0,
            "weight": weight or 0.0,
            "volume": volume or 0.0,
            "is_storable": is_storable,
        }

        # ---------- CREATE / UPDATE ----------
        if template:
            if is_storable and not template.is_storable:
                template.write({"is_storable": True})
            template.write(vals)
        else:
            template = self.env["product.template"].create(vals)

        # 🔑 asegurar que la variante existe
        self.env.flush_all()

        product_variant = self.env["product.product"].search(
            [("product_tmpl_id", "=", template.id)],
            limit=1
        )

        if not product_variant or not is_storable or stock_qty is None:
            return

        # ---------- AJUSTE DE INVENTARIO REAL ----------
        location = self.env["stock.location"].search(
            [
                ("usage", "=", "internal"),
                ("company_id", "in", [self.env.company.id, False]),
            ],
            limit=1,
        )

        quant = self.env["stock.quant"].with_context(
            inventory_mode=True,
            force_company=self.env.company.id,
        ).create({
            "product_id": product_variant.id,
            "location_id": location.id,
            "inventory_quantity": stock_qty,
        })

        # 🔴 PASO CRÍTICO: aplicar inventario
        quant.action_apply_inventory()

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _find_existing_product(self, code):
        return self.env["product.template"].search(
            [("default_code", "=", code)],
            limit=1
        )

    def _clean(self, value):
        if value in (None, ""):
            return None
        return str(value).strip()

    def _to_float(self, value):
        try:
            return float(value)
        except Exception:
            return None
