from odoo import models
from odoo.exceptions import UserError
from math import radians, sin, cos, sqrt, atan2


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def action_done(self):
        for activity in self:

            # Solo actividades de reunión
            if activity.activity_type_id.name != "Reunión":
                continue

            record = self.env[activity.res_model].browse(activity.res_id)

            # Debe haber geo del comercial
            if not record.geo_latitude or not record.geo_longitude:
                raise UserError(
                    "No puedes marcar esta actividad como hecha "
                    "si no has obtenido tu geolocalización."
                )

            # Obtener la reunión asociada

            event = self.env["calendar.event"].search([
                ("activity_ids", "in", activity.id)
            ], limit=1)

            if not event:
                continue  # si no hay reunión, no validamos distancia

            if not event.planned_latitude or not event.planned_longitude:
                continue  # reunión sin geo → no validar

            #  Calcular distancia
            distance_km = self._distance_km(
                record.geo_latitude,
                record.geo_longitude,
                event.planned_latitude,
                event.planned_longitude,
            )

            #  BLOQUEO > 500 metros
            if distance_km > 0.5:
                raise UserError(
                    f"No estás lo suficientemente cerca del punto de la reunión.\n\n"
                    f"Distancia actual: {distance_km * 1000:.0f} metros\n"
                    f"Debes estar a menos de 500 m para poder cerrarla."
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
