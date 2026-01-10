import pyodbc
from odoo.exceptions import UserError


class SaesSQLServerMixin:

    def _get_sqlserver_connection(self):
        self.ensure_one()

        try:
            conn_str = (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=localhost\\SQLEXPRESS;"
                f"DATABASE={self.database};"
                f"UID={self.user};"
                f"PWD={self.password};"
            )

            return pyodbc.connect(conn_str, timeout=5)

        except pyodbc.Error as e:
            raise UserError(
                "Error de SQL Server.\n\n"
                f"Detalle técnico:\n{e}"
            )
