from odoo.exceptions import UserError

class SaesSaleOrderImporter:
    def __init__(self, config):
        self.config = config
        self.env = config.env

    def import_sale_orders(self, limit=None):
        self._validate_config()
        rows = self._read_sale_orders(limit)

        for row in rows:
            try:
                self._import_single_order(row)
            except Exception as e:
                raise UserError(
                    f"Error importando pedido {row.get('number')}: {e}"
                )

    def _read_sale_orders(self, limit=None):
        detector = self.env["saes.detector"]
        columns = detector.detect_sale_order_columns(
            self.config,
            self.config.sale_order_table
        )

        sql_cols = []
        for key, col in columns.items():
            if col:
                if self.config.db_type == "postgres":
                    sql_cols.append(f'"{col}" AS {key}')
                else:
                    sql_cols.append(f'[{col}] AS {key}')

        if not sql_cols:
            raise UserError("No se detectaron columnas válidas de pedidos.")

        limit_sql = ""
        if limit:
            limit_sql = (
                f"LIMIT {limit}"
                if self.config.db_type == "postgres"
                else f"TOP {limit}"
            )

        query = (
            f"SELECT {', '.join(sql_cols)} FROM {self.config.sale_order_table} {limit_sql}"
            if self.config.db_type == "postgres"
            else f"SELECT {limit_sql} {', '.join(sql_cols)} FROM {self.config.sale_order_table}"
        )

        return self.config._execute_sql(query)

    def _import_single_order(self, row):
        number = row.get("number")
        date = row.get("date")
        customer_code = row.get("customer")

        if not number:
            raise UserError("Pedido sin número.")

        partner = self.env["res.partner"].search(
            [("ref", "=", customer_code)],
            limit=1
        )

        if not partner:
            raise UserError(f"Cliente no encontrado: {customer_code}")

        order = self.env["sale.order"].search(
            [("client_order_ref", "=", number)],
            limit=1
        )

        vals = {
            "partner_id": partner.id,
            "date_order": date,
            "client_order_ref": number,
        }

        if order:
            order.write(vals)
        else:
            self.env["sale.order"].create(vals)
