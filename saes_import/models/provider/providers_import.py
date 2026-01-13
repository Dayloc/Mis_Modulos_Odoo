from odoo.exceptions import UserError


class SaesProviderImporter:
    def __init__(self, config):
        self.config = config
        self.env = config.env

    # --------------------------------------------------
    # ENTRY POINT
    # --------------------------------------------------
    def import_providers(self, limit=None):
        self._validate_config()
        rows = self._read_providers(limit=limit)

        for row in rows:
            try:
                self._import_single_provider(row)
            except Exception as e:
                raise UserError(
                    f"Error importando proveedor {row.get('code')}: {e}"
                )

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------
    def _validate_config(self):
        if not self.config.provider_table:
            raise UserError("No hay tabla de proveedores seleccionada.")

    # --------------------------------------------------
    # READ PROVIDERS
    # --------------------------------------------------
    def _read_providers(self, limit=None):
        detector = self.env["saes.detector"]
        columns = detector.detect_provider_columns(
            self.config, self.config.provider_table
        )

        required = ["code", "name"]
        for r in required:
            if not columns.get(r):
                raise UserError(f"Falta columna obligatoria: {r}")

        sql_cols = []

        for key, col in columns.items():
            if not col:
                continue

            if self.config.db_type == "postgres":
                sql_cols.append(f'"{col}" AS {key}')
            else:
                sql_cols.append(f'[{col}] AS {key}')

        # --------------------------------------------------
        # TELÉFONOS DESDE TELF_PRO
        # --------------------------------------------------
        if self.config.db_type != "postgres":
            # Teléfono principal (LINEA = 1)
            sql_cols.append(
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_PRO t
                    WHERE t.PROVEEDOR = {self.config.provider_table}.CODIGO
                      AND t.LINEA = 1
                ) AS phone"""
            )

            # Móvil (LINEA = 3)
            sql_cols.append(
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_PRO t
                    WHERE t.PROVEEDOR = {self.config.provider_table}.CODIGO
                      AND t.LINEA = 3
                ) AS mobile"""
            )

            # Fax (LINEA = 2)
            sql_cols.append(
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_PRO t
                    WHERE t.PROVEEDOR = {self.config.provider_table}.CODIGO
                      AND t.LINEA = 2
                ) AS fax"""
            )

            # Teléfono extra (LINEA >= 4)
            sql_cols.append(
                f"""(
                    SELECT TOP 1 LTRIM(RTRIM(t.TELEFONO))
                    FROM TELF_PRO t
                    WHERE t.PROVEEDOR = {self.config.provider_table}.CODIGO
                      AND t.LINEA >= 4
                ) AS extra_phone"""
            )

        limit_sql = ""
        if limit:
            limit_sql = (
                f"LIMIT {limit}"
                if self.config.db_type == "postgres"
                else f"TOP {limit}"
            )

        if self.config.db_type == "postgres":
            query = f"""
                SELECT {", ".join(sql_cols)}
                FROM {self.config.provider_table}
                {limit_sql}
            """
        else:
            query = f"""
                SELECT {limit_sql} {", ".join(sql_cols)}
                FROM {self.config.provider_table}
            """

        return self.config._execute_sql(query)

    # --------------------------------------------------
    # IMPORT SINGLE PROVIDER
    # --------------------------------------------------
    def _import_single_provider(self, row):
        code = self.config._normalize_code(row.get("code"))
        name = (row.get("name") or "").strip()

        if not code:
            raise UserError("Proveedor sin código.")

        partner = self._find_existing_partner(code)

        # ---------- TELÉFONOS ----------
        phone = self._normalize_phone(row.get("phone"))
        mobile = self._normalize_phone(row.get("mobile"))
        fax = self._normalize_phone(row.get("fax"))
        extra_phone = self._normalize_phone(row.get("extra_phone"))

        vat = (row.get("vat") or "").strip().upper()

        # ---------- NOTAS ----------
        notes = []

        observaciones = (row.get("observaciones") or "").strip()
        if observaciones:
            notes.append(observaciones)

        if vat:
            notes.append(f"VAT/CIF: {vat}")

        if fax:
            notes.append(f"Fax: {fax}")

        if extra_phone:
            notes.append(f"Teléfono extra: {extra_phone}")

        # ---------- PROVINCIA ----------
        state = self._find_state_by_name(row.get("state"))

        Partner = self.env["res.partner"]
        has_supplier_rank = "supplier_rank" in Partner._fields

        vals = {
            "ref": code,
            "name": name or f"Proveedor {code}",
            "email": row.get("email"),
            "street": row.get("street"),
            "zip": row.get("zip"),
            "city": row.get("city"),
            "state_id": state.id if state else False,
            "phone": phone,
            "mobile": mobile,
            "is_company": True,
        }

        if has_supplier_rank:
            vals["supplier_rank"] = 1

        # ---------- NOTAS SIN DUPLICAR ----------
        if partner and partner.comment:
            notes = [n for n in notes if n not in partner.comment]

        if notes:
            note_text = "\n".join(notes)
            vals["comment"] = (
                partner.comment + "\n" + note_text
                if partner and partner.comment
                else note_text
            )

        # ---------- CREATE / UPDATE ----------
        if partner:
            partner.write(vals)
        else:
            self.env["res.partner"].create(vals)

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------
    def _find_existing_partner(self, code):
        return self.env["res.partner"].search(
            [("ref", "=", code)],
            limit=1
        )

    def _normalize_phone(self, value):
        if not value:
            return None
        return "".join(c for c in str(value) if c.isdigit()) or None

    def _find_state_by_name(self, state_name):
        if not state_name:
            return None

        return self.env["res.country.state"].search(
            [("name", "ilike", state_name.strip())],
            limit=1
        )
