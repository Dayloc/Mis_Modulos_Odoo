from odoo import models
from odoo.exceptions import UserError


class SaesDetector(models.AbstractModel):
    _name = "saes.detector"
    _description = "Detector automático de estructura SAE"

    def _fetch_tables_postgres(self, conn):
        cur = conn.cursor()
        cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """)
        return [r[0] for r in cur.fetchall()]

    def _fetch_tables_sqlserver(self, conn):
        cur = conn.cursor()
        cur.execute("""
                    SELECT name
                    FROM sys.tables
                    """)
        return [r[0] for r in cur.fetchall()]

    def detect_tables(self, config):
        if config.db_type == "postgres":
            conn = config._get_saes_connection()
            try:
                return self._fetch_tables_postgres(conn)
            finally:
                conn.close()

        elif config.db_type == "sqlserver":
            conn = config._get_sqlserver_connection()
            try:
                return self._fetch_tables_sqlserver(conn)
            finally:
                conn.close()

        else:
            raise UserError("Tipo de base de datos no soportado.")

    # detectar tablas candidatas a cliente
    def detect_client_tables(self, config):
        tables = self.detect_tables(config)

        keywords = [
            "cliente", "clientes",
            "customer", "customers",
            "cust",
            "sn_cliente",
            "cont_cli",
        ]

        candidates = []
        for table in tables:
            t = table.lower()
            if any(k in t for k in keywords):
                candidates.append(table)

        return candidates

    def detect_columns(self, config, table_name):
        """
        Devuelve una lista de nombres de columnas de una tabla,
        funcionando para PostgreSQL y SQL Server
        """

        # PostgreSQL
        if config.db_type == "postgres":
            conn = config._get_saes_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = %s
                            """, (table_name,))
                return [r[0] for r in cur.fetchall()]
            finally:
                cur.close()
                conn.close()

        # SQL Server
        elif config.db_type == "sqlserver":
            conn = config._get_sqlserver_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                            SELECT COLUMN_NAME
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_NAME = ?
                            """, table_name)
                return [r[0] for r in cur.fetchall()]
            finally:
                cur.close()
                conn.close()

        else:
            return []

    # detectar columnas claves en clientes
    def detect_client_columns(self, config, table):
        columns = self.detect_columns(config, table)

        mapping = {
            "code": None,
            "name": None,
            "email": None,
            "street": None,
            "zip": None,
            "city": None,
            "pais": None,
            "state": None,
            "phone": None,
            "mobile": None,
            "vat": None,
            "name2": None,
        }

        keywords = {
            "code": ["codigo", "code", "cve", "id_cliente", "cliente"],
            "name": ["nombre", "name", "razon", "empresa"],
            "email": ["email", "mail", "correo"],
            "street": ["direccion", "dir", "address", "calle"],
            "zip": ["cp", "zip", "postal", "codpost"],
            "city": ["ciudad", "city", "poblacion"],
            "pais": ["pais", "country", "prefijo", "codpais"],
            "state": ["provincia", "estado", "state", "region"],
            "phone": ["telefono", "tel", "phone", "fijo"],
            "mobile": ["movil", "mobile", "celular"],
            "vat": ["cif", "nif", "vat", "dni"],
            "name2": ["nombre2", "razon2", "nombre_2", "denominacion2"]


        }

        for col in columns:
            c = col.lower()
            for field, keys in keywords.items():
                if mapping[field] is None and any(k in c for k in keys):
                    mapping[field] = col

        return mapping

    # detector de provedores
    def detect_provider_tables(self, config):
        tables = self.detect_tables(config)

        keywords = [

            "proveedor","proveedores", "prov",
            "prov.","vendedor","vendedores",

            "supplier", "suppliers",
            "vendor","vendors",
        ]

        return [
            t for t in tables
            if any(k in t.lower() for k in keywords)
        ]

    def detect_provider_columns(self, config, table):
        columns = self.detect_columns(config, table)

        mapping = {
            "code": None,
            "name": None,
            "email": None,
            "street": None,
            "vat": None,
            "zip": None,
            "city": None,
            "state": None,
            "observaciones": None,
        }

        keywords = {
            "code": ["codigo", "code", "id", "proveedor"],
            "name": ["nombre", "name", "razon", "empresa"],
            "email": ["email", "mail", "correo"],
            "vat": ["cif", "nif", "vat", "dni"],
            "street": ["direccion", "dir", "address", "calle"],
            "zip": ["cp", "zip", "postal", "codpost"],
            "city": ["ciudad", "city", "poblacion"],
            "state": ["provincia", "estado", "state"],
            "observaciones": ["observaciones", "obs", "comentarios", "notas"],

        }

        for col in columns:
            c = col.lower()
            for field, keys in keywords.items():
                if mapping[field] is None and any(k in c for k in keys):
                    mapping[field] = col

        return mapping

    # detectar tabla productos
    def detect_product_tables(self, config):
        tables = self.detect_tables(config)

        keywords = [
            "producto", "productos",
            "articulo", "articulos",
            "item", "items","product", "products","art",
            "stock",
        ]

        candidates = {
            t for t in tables
            if any(k in t.lower() for k in keywords)
        }

        return sorted(candidates)

    # detector de columnas de producto
    def detect_product_columns(self, config, table):
        columns = self.detect_columns(config, table)

        mapping = {
            "code": None,
            "name": None,
            "name2": None,
            "description": None,
            "family": None,
            "brand": None,
            "price": None,
            "cost": None,
            "active": None,
            "type": None,
            "weight": None,
            "volume": None,
            "stock": None,
            "vat": None,
        }

        keywords = {
            "code": ["codigo", "cod"],
            "name": ["nombre"],
            "name2": ["nombre2"],
            "description": ["observ", "carac", "definicion"],
            "family": ["familia", "subfamilia"],
            "brand": ["marca"],
            "price": ["pvp", "precio", "importe", "pmcom"],
            "cost": ["cost_ult", "cost"],
            "active": ["baja"],
            "type": ["tipo_art"],
            "weight": ["peso"],
            "volume": ["litros"],
            "stock": ["stock"],
            "vat": ["tipo_iva", "grupoiva"],
        }

        for col in columns:
            c = col.lower()
            for field, keys in keywords.items():
                if mapping[field] is None and any(k in c for k in keys):
                    mapping[field] = col

        return mapping

    # detectar tablas de pedidos
    def detect_sale_order_tables(self, config):

        tables = self.detect_tables(config)

        # palabras clave claras de pedidos
        keywords = [

            "pedido", "pedidos",
            "pedido_venta", "ped_venta", "ped_ven", "pedv",
            "orden", "ordenes", "orden_venta",
            "venta", "ventas","presupuesto", "presupuestos", "pres",
            "cotizacion", "cotizaciones", "cotiza",
            "numped", "num_ped", "nroped", "folio",
            "pedido_cliente", "ped_cli","order", "orders",
            "sale_order", "sales_order", "salesorder","so", "so_header", "so_master", "so_hdr",
            "quotation", "quote", "estimate","customer_order", "customerorder","ped", "peds","pedico","ord", "ordv","sl_order",
            "salord",
        ]

        # exclusiones claras
        blacklist = [
            "com", "prov", "cont", "fact",
            "stock", "alma", "iva", "ret",
            "banco", "cli", "prove",
        ]

        candidates = []

        for table in tables:
            t = table.lower()

            # fuera cabeceras y bancos SIEMPRE
            if t.startswith(( "b_", "d_")):
                continue

            # fuera basura conocida
            if any(b in t for b in blacklist):
                continue

            # solo si contiene palabras de pedido
            if any(k in t for k in keywords):
                candidates.append(table)

        return sorted(set(candidates))

    def detect_sale_order_columns(self, config, table):
        columns = self.detect_columns(config, table)

        mapping = {
            "number": None,
            "date": None,
            "customer": None,
            "total": None,
            "state": None,
        }

        keywords = {
            "number": {
                "strong": [
                    "numero", "num_pedido", "numped",
                    "pedido", "folio"
                ],
                "weak": [
                    "num"
                ],
            },
            "date": {
                "strong": [
                    "fecha"
                ],
                "weak": [
                    "date"
                ],
            },
            "customer": {
                "strong": [
                    "empresa", "cliente", "customer"
                ],
                "weak": [
                    "proveedor", "prov"
                ],
            },
            "total": {
                "strong": [
                    "totalped", "totaldoc", "totaldiv"
                ],
                "weak": [
                    "total", "importe"
                ],
            },
            "state": {
                "strong": [
                    "cancelado", "traspasado", "pronto"
                ],
                "weak": [
                    "estado", "status"
                ],
            },
        }

        # primero strong
        for field, groups in keywords.items():
            for col in columns:
                c = col.lower()
                if any(k in c for k in groups["strong"]):
                    mapping[field] = col
                    break

        # luego weak
        for field, groups in keywords.items():
            if mapping[field]:
                continue
            for col in columns:
                c = col.lower()
                if any(k in c for k in groups["weak"]):
                    mapping[field] = col
                    break

        return mapping
    # normalizar país con code
    def _normalize_code(self, value):
        return value.strip().upper() if value else None
    #detectar tablas de líneas
    def detect_sale_order_line_tables(self, config):
        tables = self.detect_tables(config)

        # keywords fuertes de líneas
        keywords = [
            # genérico
            "linea", "lineas",
            "detalle", "det", "detal",
            "item", "items",
            "row", "rows",
            "pos", "position",

            # pedidos
            "pedido_linea", "pedido_det", "pedido_lin",
            "ped_lin", "ped_line", "ped_det",
            "order_line", "order_lines",
            "sale_order_line", "sales_order_line",
            "so_line", "so_lines",

            # legacy / español
            "renglon", "renglones",
            "concepto", "conceptos",
        ]

        # blacklist MUY importante
        blacklist = [
            # cabeceras
            "cab", "header", "head",
            "maestro", "master",

            # otros documentos
            "fact", "invoice",
            "albaran", "delivery",
            "compra", "purchase",

            # stock / contabilidad
            "stock", "mov", "movim",
            "almacen", "warehouse",
            "contab", "iva", "impuesto",

            # claramente NO líneas
            "cliente", "proveedor",
            "producto", "articulo",
            "precio", "tarifa",
            "tmp", "temp", "log", "hist",
        ]

        candidates = []

        for table in tables:
            t = table.lower()

            # debe contener keyword de líneas
            if not any(k in t for k in keywords):
                continue

            #  NO debe caer en blacklist
            if any(b in t for b in blacklist):
                continue

            # opcional: debe tener datos
            if hasattr(self, "_table_has_data"):
                if not self._table_has_data(config, table):
                    continue

            candidates.append(table)

        return sorted(set(candidates))

    # detectar tablas facturas de venta
    def detect_sale_invoice_tables(self, config):
        tables = self.detect_tables(config)

        keywords = [
            # español
            "fact", "factura", "facturas",
            "fac_ven", "fact_ven", "factv",
            "c_fact", "c_factven",

            # inglés
            "invoice", "invoices",
            "sales_invoice", "sale_invoice",
            "inv_sale",

            # sage / legacy
            "c_factura", "c_factven",
            "sn_facven", "sn_factven",
        ]

        blacklist = [
            # líneas
            "line", "linea", "detalle",

            # compras
            "compra", "purchase", "prov",

            # basura
            "tmp", "temp", "hist", "log",
        ]

        candidates = []

        for table in tables:
            t = table.lower()

            if not any(k in t for k in keywords):
                continue
            if any(b in t for b in blacklist):
                continue

            candidates.append(table)

        return sorted(set(candidates))
    # detectar tablas facturas de compras
    def detect_purchase_invoice_tables(self, config):
        tables = self.detect_tables(config)

        keywords = [
            # español
            "fact", "factura", "facturas",
            "fac_com", "fact_com",

            # inglés
            "purchase_invoice", "supplier_invoice",
            "invoice_purchase",

            # sage / legacy
            "sn_faccom", "sn_factcom",
            "p_fact", "prov_fact",
        ]

        blacklist = [
            # líneas
            "line", "linea", "detalle",

            # ventas
            "venta", "sale", "cliente",

            # basura
            "tmp", "temp", "hist", "log",
        ]

        candidates = []

        for table in tables:
            t = table.lower()

            if not any(k in t for k in keywords):
                continue
            if any(b in t for b in blacklist):
                continue

            candidates.append(table)

        return sorted(set(candidates))

    def detect_invoice_columns(self, config, table):
        conn = config._get_connection()
        try:
            cur = conn.cursor()

            if config.db_type == "postgres":
                cur.execute(f'SELECT * FROM "{table}" LIMIT 1')
            else:
                cur.execute(f"SELECT TOP 1 * FROM [{table}]")

            columns = [c[0].lower() for c in cur.description]
        finally:
            conn.close()

        def find(*keys):
            for col in columns:
                for key in keys:
                    if key in col:
                        return col
            return None

        return {
            # identificadores
            "number": find("num", "number", "factura", "invoice", "doc"),
            "date": find("fecha", "date", "data", "dt"),
            "customer_code": find("cliente", "customer", "codcli", "idcli"),
            "customer_name": find("nombre", "name", "cliente"),

            # importes
            "amount_untaxed": find("base", "subtotal", "neto"),
            "amount_tax": find("iva", "tax", "impuesto"),
            "amount_total": find("total", "importe"),

            # estado / referencia
            "state": find("estado", "status"),
            "currency": find("moneda", "currency"),
            "origin": find("pedido", "order", "origen", "ref"),
        }