import json
import os

from odoo.exceptions import UserError


class SaesClientImporter:
    def __init__(self, config):
        self.config = config
        self.env = config.env
        self.country_map = self._load_country_map()

    # ==========================================================
    # IMPORT
    # ==========================================================
    def import_clients(self, limit=None):
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

    # ==========================================================
    # READ CLIENTS
    # ==========================================================
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

        if self.config.db_type != "postgres":
            sql_cols.extend([
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_CLI t
                    WHERE t.CLIENTE = {self.config.client_table}.CODIGO
                      AND t.LINEA = 1
                ) AS phone""",
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_CLI t
                    WHERE t.CLIENTE = {self.config.client_table}.CODIGO
                      AND t.LINEA = 3
                ) AS mobile""",
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_CLI t
                    WHERE t.CLIENTE = {self.config.client_table}.CODIGO
                      AND t.LINEA = 2
                ) AS fax""",
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_CLI t
                    WHERE t.CLIENTE = {self.config.client_table}.CODIGO
                      AND t.LINEA = 4
                ) AS extra_phone"""
            ])

        limit_sql = ""
        if limit:
            limit_sql = f"LIMIT {limit}" if self.config.db_type == "postgres" else f"TOP {limit}"

        query = (
            f"SELECT {', '.join(sql_cols)} FROM {self.config.client_table} {limit_sql}"
            if self.config.db_type == "postgres"
            else f"SELECT {limit_sql} {', '.join(sql_cols)} FROM {self.config.client_table}"
        )

        return self.config._execute_sql(query)

    # ==========================================================
    # MAIN IMPORT LOGIC
    # ==========================================================
    def _import_all_clients_importer(self, row):
        code = self.config._normalize_code(row.get("code"))
        if not code:
            raise UserError("Cliente sin código.")

        name1 = (row.get("name") or "").strip()
        name2 = (row.get("name2") or "").strip()
        full_name = f"{name1} - {name2}" if name1 and name2 else name1 or f"Cliente {code}"

        partner = self._find_existing_partner(code)

        # -------------------------
        # COUNTRY
        # -------------------------
        phone_code = self._normalize_phone_code(row.get("pais"))
        country = self._find_country_by_phone_code(phone_code)

        if not country:
            zip_code = (row.get("zip") or "").strip()
            if zip_code.isdigit() and "01" <= zip_code[:2] <= "52":
                country = self.env["res.country"].search(
                    [("code", "=", "ES")],
                    limit=1
                )

        # -------------------------
        # STATE
        # -------------------------
        state = self._find_state_by_name(country, row.get("state"))

        # -------------------------
        # PHONES
        # -------------------------
        phone = self._build_international_phone(phone_code, row.get("phone"))
        mobile = self._build_international_phone(phone_code, row.get("mobile"))

        # -------------------------
        # VAT / AUX ACCOUNT
        # -------------------------
        vat_to_save = None
        aux_account = None

        raw_vat = self._normalize_vat(row.get("vat"), country)

        if raw_vat:
            if country and country.code == "ES":
                vat_no_prefix = raw_vat.replace("ES", "")

                if (
                    self._is_nif(vat_no_prefix)
                    or self._is_nie(vat_no_prefix)
                    or self._is_cif(vat_no_prefix)
                ):
                    vat_to_save = raw_vat
                else:
                    aux_account = raw_vat
            else:
                try:
                    self.env["res.partner"]._check_vat(raw_vat, country=country)
                    vat_to_save = raw_vat
                except Exception:
                    aux_account = raw_vat

        # -------------------------
        # VALUES
        # -------------------------
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
            "phone": phone,
            "mobile": mobile,
            "x_aux_account": aux_account,
        }

        if vat_to_save:
            vals["vat"] = vat_to_save

        if partner:
            partner.write(vals)
        else:
            self.env["res.partner"].create(vals)

    # ==========================================================
    # HELPERS
    # ==========================================================
    def _find_existing_partner(self, code):
        return self.env["res.partner"].search(
            [("ref", "=", code)],
            limit=1
        )

    def _normalize_phone_code(self, value):
        return str(value).replace("+", "").strip() if value else None

    def _normalize_phone_number(self, value):
        return "".join(c for c in str(value) if c.isdigit()) if value else None

    def _build_international_phone(self, phone_code, number):
        number = self._normalize_phone_number(number)
        if not number:
            return None
        return f"+{phone_code}{number}" if phone_code else number

    def _normalize_vat(self, value, country):
        if not value:
            return None
        vat = str(value).strip().upper().replace(" ", "")
        if country and country.code == "ES" and not vat.startswith("ES"):
            vat = f"ES{vat}"
        return vat

    # ==========================================================
    # VAT VALIDATORS (ES)
    # ==========================================================
    def _is_nif(self, vat):
        if not vat or len(vat) != 9:
            return False
        number = vat[:8]
        letter = vat[8]
        if not number.isdigit():
            return False
        letters = "TRWAGMYFPDXBNJZSQVHLCKE"
        return letters[int(number) % 23] == letter

    def _is_nie(self, vat):
        if not vat or len(vat) != 9:
            return False
        if vat[0] not in "XYZ":
            return False
        number = str("XYZ".index(vat[0])) + vat[1:8]
        letters = "TRWAGMYFPDXBNJZSQVHLCKE"
        return letters[int(number) % 23] == vat[8]

    def _is_cif(self, vat):
        if not vat or len(vat) != 9:
            return False

        letter = vat[0]
        digits = vat[1:8]
        control = vat[8]

        if not digits.isdigit():
            return False

        even_sum = sum(int(d) for d in digits[1::2])
        odd_sum = 0
        for d in digits[0::2]:
            tmp = int(d) * 2
            odd_sum += tmp // 10 + tmp % 10

        total = even_sum + odd_sum
        control_digit = (10 - (total % 10)) % 10
        control_letter = "JABCDEFGHI"[control_digit]

        if letter in "PQRSNW":
            return control == control_letter
        if letter in "ABEH":
            return control == str(control_digit)

        return control in (str(control_digit), control_letter)

    # ==========================================================
    # COUNTRY / STATE
    # ==========================================================
    def _find_country_by_phone_code(self, phone_code):
        if not phone_code:
            return None

        country = self.env["res.country"].search(
            [("phone_code", "=", phone_code)],
            limit=1
        )
        if country:
            return country

        code = self.country_map.get(phone_code)
        return (
            self.env["res.country"].search([("code", "=", code)], limit=1)
            if code
            else None
        )

    def _find_state_by_name(self, country, name):
        if not country or not name:
            return None

        return self.env["res.country.state"].search(
            [
                ("country_id", "=", country.id),
                ("name", "ilike", name.strip()),
            ],
            limit=1
        )

    # ==========================================================
    # COUNTRY MAP
    # ==========================================================
    def _load_country_map(self):
        path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "data",
                "country_code_map.json",
            )
        )

        if not os.path.exists(path):
            raise UserError(f"No se encuentra el JSON: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
