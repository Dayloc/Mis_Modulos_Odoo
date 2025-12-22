from odoo import models
from odoo.exceptions import UserError
from math import radians, sin, cos, sqrt, atan2


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def action_done(self):
        for activity in self:

            # Solo reuniones
            if activity.activity_type_id.name != "Reunión":
                continue

            # Evento asociado
            event = self.env["calendar.event"].search([
                ("activity_ids", "in", activity.id)
            ], limit=1)

            if not event:
                continue

            # 1️⃣ Si no hay GEO del comercial → obtenerla
            if not event.done_latitude or not event.done_longitude:
                return {
                    "type": "ir.actions.client",
                    "tag": "calendar_user_geo",
                    "context": {
                        "active_model": "calendar.event",
                        "active_id": event.id,
                    },
                }

            # 2️⃣ SI NO HAY GEO PLANIFICADA → permitir cerrar (NO validar)
            if not event.planned_latitude or not event.planned_longitude:
                continue

            # 3️⃣ Validar distancia
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

        return super().action_done()

    def _distance_km(self, lat1, lon1, lat2, lon2):
        R = 6371.0

        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c
