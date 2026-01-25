from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, time


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    archived = fields.Boolean(string="Archivado", default=False)
    auto_generated = fields.Boolean(string="Generado Automáticamente", default=False)

    x_worked_time_calculated = fields.Float(
        string="Tiempo Calculado",
        compute='_compute_worked_time_calculated',
        store=True,
        help="Calcula las horas trabajadas directamente de la entrada y salida."
    )

    @api.depends('check_in', 'check_out')
    def _compute_worked_time_calculated(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                attendance.x_worked_time_calculated = delta.total_seconds() / 3600.0
            else:
                attendance.x_worked_time_calculated = 0.0

    @api.depends('x_worked_time_calculated')
    def _compute_worked_hours(self):
        for attendance in self:
            attendance.worked_hours = attendance.x_worked_time_calculated

    # validacion para si ya existe un registro de un día para un usuario, no permitir volver a registrar
    @api.constrains('employee_id', 'check_in', 'check_out')
    def _check_single_check_in_per_day(self):
        for attendance in self:
            # 🔒 SOLO validar cuando hay check_in NUEVO
            if not attendance.check_in:
                continue

            # 👉 Si ya existe check_out y solo estamos cerrando, NO validar
            if attendance.check_out:
                continue

            day_start = datetime.combine(attendance.check_in.date(), time.min)
            day_end = datetime.combine(attendance.check_in.date(), time.max)

            domain = [
                ('id', '!=', attendance.id),
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '>=', day_start),
                ('check_in', '<=', day_end),
            ]

            if self.search_count(domain):
                raise ValidationError(_(
                    "Ya existe un registro de entrada para este empleado en el día %s."
                ) % attendance.check_in.date().strftime('%d/%m/%Y'))
