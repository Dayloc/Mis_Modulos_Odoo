from odoo import models, fields
from datetime import timedelta
import calendar
from dateutil.relativedelta import relativedelta

class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    delay_type = fields.Selection(
        selection_add=[
            ('days_after_fixed_day', 'Days after invoice date on the fixed day'),
        ],
        ondelete={'days_after_fixed_day': 'set default'},
    )

    payment_day = fields.Integer(
        string="Día de pago",
        help="Día del mes en el que debe caer el pago (1-28/30/31)."
    )

    def _get_due_date(self, date_ref):
        self.ensure_one()
        due_date = fields.Date.from_string(date_ref) or fields.Date.today()

        if self.delay_type == 'days_after_fixed_day':
            base_date = due_date + relativedelta(days=self.nb_days or 0)

            if not self.payment_day:
                return base_date

            # Mes y año del vencimiento
            year = base_date.year
            month = base_date.month

            # Si el día base ya pasó, usar mes siguiente
            if base_date.day > self.payment_day:
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1

            # Ajustar al último día si el mes no tiene el payment_day
            last_day_of_month = calendar.monthrange(year, month)[1]
            day = min(self.payment_day, last_day_of_month)

            return base_date.replace(year=year, month=month, day=day)

        # Llamar al método nativo para los demás tipos
        return super()._get_due_date(date_ref)