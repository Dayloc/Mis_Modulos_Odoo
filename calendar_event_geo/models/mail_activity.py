from odoo import models
from odoo.exceptions import UserError, RedirectWarning
from math import radians, sin, cos, sqrt, atan2


class MailActivity(models.Model):
    _inherit = "mail.activity"

    # Lógica común reutilizable
    def _check_geo(self):
        for activity in self:

            # Solo actividades tipo Reunión
            if activity.activity_type_id.name != "Reunión":
                continue

            # Evento asociado
            event = self.env["calendar.event"].search([
                ("activity_ids", "in", activity.id)
            ], limit=1)

            if not event:
                continue

            #  No hay GEO real  pedirla
            if not event.done_latitude or not event.done_longitude:
                raise RedirectWarning(
                    "Es necesario obtener tu ubicación para cerrar la reunión.",
                    {
                        "type": "ir.actions.client",
                        "tag": "calendar_user_geo",
                        "context": {
                            "active_model": "calendar.event",
                            "active_id": event.id,
                        },
                    },
                    "Obtener ubicación"
                )

            #  No hay GEO planificada  permitir cerrar
            if not event.planned_latitude or not event.planned_longitude:
                continue

            # Validar distancia
            distance_km = self._distance_km(
                event.done_latitude,
                event.done_longitude,
                event.planned_latitude,
                event.planned_longitude,
            )

            if distance_km > 0.5:
                raise UserError(
                    "No estás lo suficientemente cerca del punto de la reunión.\n\n"
                    f"Distancia actual: {distance_km * 1000:.0f} metros\n"
                    "Debes estar a menos de 500 m para poder cerrarla."
                )

    # Usado por vistas tipo lista
    def action_done(self):
        self._check_geo()
        return super().action_done()

    # Usado INTERNAMENTE por chatter, feedback, etc.
    def _action_done(self, *args, **kwargs):
        self._check_geo()
        return super()._action_done(*args, **kwargs)

    # Cálculo de distancia
    def _distance_km(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1, lon1 = radians(lat1), radians(lon1)
        lat2, lon2 = radians(lat2), radians(lon2)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return R * (2 * atan2(sqrt(a), sqrt(1 - a)))
