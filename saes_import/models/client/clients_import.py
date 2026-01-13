import json
import os

from odoo.exceptions import UserError

class SaesClientImporter:
    def __init__(self, config):
        self.config = config
        self.env = config.env
        self.country_map = self._load_country_map()

    def import_clients(self, limit=None):
        """
        Importa clientes desde la tabla seleccionada
        """
        self._validate_config()
        rows = self._read_clients(limit=limit)

        for row in rows:
            try:
                self._import_all_clients_importer(row)
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
                if key == "pais" and self.config.db_type != "postgres":
                    sql_cols.append(
                        f"LTRIM(RTRIM(CAST([{col}] AS VARCHAR(5)))) AS {key}"
                    )
                else:
                    sql_cols.append(f'[{col}] AS {key}')

        # teléfono cuando LINEA = 1
        if self.config.db_type != "postgres":
            sql_cols.append(
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_CLI t
                    WHERE t.CLIENTE = {self.config.client_table}.CODIGO
                      AND t.LINEA = 1
                ) AS phone"""
            )

        # movil para  (LINEA = 2)
        if self.config.db_type != "postgres":
            sql_cols.append(
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_CLI t
                    WHERE t.CLIENTE = {self.config.client_table}.CODIGO
                      AND t.LINEA = 3
                ) AS mobile"""
            )
        # fax (LINEA = 2)
        if self.config.db_type != "postgres":
                sql_cols.append(
                    f"""(
                        SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                        FROM TELF_CLI t
                        WHERE t.CLIENTE = {self.config.client_table}.CODIGO
                          AND t.LINEA = 2
                    ) AS fax"""
                )
        # teléfono extra (LINEA = 4)
        if self.config.db_type != "postgres":
                    sql_cols.append(
                        f"""(
                            SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                            FROM TELF_CLI t
                            WHERE t.CLIENTE = {self.config.client_table}.CODIGO
                              AND t.LINEA = 4
                        ) AS extra_phone"""
                    )

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

    def _import_all_clients_importer(self, row):

        code = self.config._normalize_code(row.get("code"))
        if not code:
            raise UserError("Cliente sin código.")

        name1 = (row.get("name") or "").strip()
        name2 = (row.get("name2") or "").strip()
        full_name = (
            f"{name1} - {name2}"
            if name1 and name2
            else name1 or f"Cliente {code}"
        )

        partner = self._find_existing_partner(code)

        # =========================
        # PAÍS
        # =========================
        phone_code = self._normalize_phone_code(row.get("pais"))
        country = self._find_country_by_phone_code(phone_code)

        # fallback por CP → España
        if not country:
            zip_code = (row.get("zip") or "").strip()
            if zip_code.isdigit() and len(zip_code) >= 2:
                if "01" <= zip_code[:2] <= "52":
                    country = self.env["res.country"].search(
                        [("code", "=", "ES")],
                        limit=1
                    )

        # fallback por prefijo VAT
        raw_vat = self._normalize_vat(row.get("vat"))
        if not country and raw_vat and raw_vat[:2].isalpha():
            country = self.env["res.country"].search(
                [("code", "=", raw_vat[:2].upper())],
                limit=1
            )

        # =========================
        # PROVINCIA
        # =========================
        state = self._find_state_by_name(country, row.get("state"))

        # =========================
        # TELÉFONOS
        # =========================
        phone_full = self._build_international_phone(phone_code, row.get("phone"))
        mobile_full = self._build_international_phone(phone_code, row.get("mobile"))
        fax_full = self._build_international_phone(phone_code, row.get("fax"))
        extra_phone_full = self._build_international_phone(
            phone_code, row.get("extra_phone")
        )

        # =========================
        # NOTAS
        # =========================
        extra_notes = []

        if not country and phone_code:
            extra_notes.append(f"Código de país no reconocido: {phone_code}")

        if fax_full:
            extra_notes.append(f"Fax: {fax_full}")

        if extra_phone_full:
            extra_notes.append(f"Teléfono extra: {extra_phone_full}")

        # =========================
        # VAT / CUENTA AUXILIAR (CLAVE)
        # =========================
        vat_to_save = None
        aux_account = None

        if raw_vat:
            try:
                # intentamos validar con Odoo
                self.env["res.partner"]._check_vat(raw_vat, country=country)
                vat_to_save = raw_vat
            except Exception:
                # si NO es válido → NO romper Odoo
                aux_account = raw_vat

        # =========================
        # VALORES PARTNER
        # =========================
        Partner = self.env["res.partner"]
        has_customer_rank = "customer_rank" in Partner._fields

        vals = {
            "ref": code,
            "name": full_name,
            "email": row.get("email"),
            "street": row.get("street"),
            "zip": row.get("zip"),
            "city": row.get("city"),
            "is_company": True,
            "country_id": country.id if country else False,
            "state_id": state.id if state else False,
            "phone": phone_full,
            "mobile": mobile_full,
            "vat": vat_to_save,
            "x_aux_account": aux_account,
        }

        if has_customer_rank:
            vals["customer_rank"] = 1

        # =========================
        # EVITAR DUPLICAR NOTAS
        # =========================
        if partner and partner.comment:
            extra_notes = [
                note for note in extra_notes
                if note not in partner.comment
            ]

        if extra_notes:
            note = "\n".join(extra_notes)
            vals["comment"] = (
                partner.comment + "\n" + note
                if partner and partner.comment
                else note
            )

        # =========================
        # CREATE / UPDATE
        # =========================
        if partner:
            partner.write(vals)
        else:
            Partner.create(vals)

    def _find_existing_partner(self, code):
        return self.env["res.partner"].search(
            [("ref", "=", code)],
            limit=1
        )
    # metodos para convertir código a país
    def _normalize_phone_code(self, value):
        if not value:
            return None

        value = str(value).strip()
        value = value.replace("+", "")
        #value = value.lstrip("0")

        return value or None

    def _find_country_by_phone_code(self, phone_code):
        if not phone_code:
            return None

        # 1️ Buscar en Odoo (phone_code real)
        country = self.env["res.country"].search(
            [("phone_code", "=", phone_code)],
            limit=1
        )
        if country:
            return country

        # Buscar en nuestro archivo json propio
        country_code = self.country_map.get(phone_code)
        if country_code:
            return self.env["res.country"].search(
                [("code", "=", country_code)],
                limit=1
            )

        return None

    def _find_state_by_name(self, country, state_name):
        if not country or not state_name:
            return None

        return self.env["res.country.state"].search(
            [
                ("country_id", "=", country.id),
                ("name", "ilike", state_name.strip()),
            ],
            limit=1
        )

        # normalizar número de teléfono
    def _normalize_phone_number(self, value):
            if not value:
                return None

            value = str(value)
            return "".join(c for c in value if c.isdigit())

    # construir el numero de teléfono
    def _build_international_phone(self, phone_code, number):
        if not number:
            return None

        number = self._normalize_phone_number(number)

        if not number:
            return None

        if phone_code:
            return f"+{phone_code}{number}"

        return number

        # CIF normalización
    def _normalize_vat(self, value):
            if not value:
                return None
            return str(value).strip().upper()

    # validar cif
    def _is_cif(self, vat):
        if not vat:
            return False
        vat = vat.strip().upper()
        return (
                len(vat) == 9
                and vat[0].isalpha()
                and vat[1:].isdigit()
        )
    # validar nif
    def _is_nif(self, vat):
        if not vat:
            return False
        vat = vat.strip().upper()
        return (
                len(vat) == 9
                and vat[:8].isdigit()
                and vat[8].isalpha()
        )

    # buscar pais en json
    def _load_country_map(self):
        path = os.path.join(
            os.path.dirname(__file__),  # models/client/
            "..",  # models/
            "..",  # saes_import/
            "data",
            "country_code_map.json"
        )
        path = os.path.abspath(path)

        if not os.path.exists(path):
            raise UserError(f"NO SE ENCUENTRA EL JSON: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

