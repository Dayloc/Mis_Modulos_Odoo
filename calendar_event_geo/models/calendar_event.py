from odoo import models, fields, _
from odoo.exceptions import UserError
from math import radians, sin, cos, sqrt, atan2
from markupsafe import Markup
import requests


class CalendarEvent(models.Model):
    _inherit = "calendar.event"


    #  Ubicación planificada de la reunión

    planned_latitude = fields.Float(string="Latitud reunión")
    planned_longitude = fields.Float(string="Longitud reunión")


    #  Ubicación real del comercial

    done_latitude = fields.Float(string="Latitud comercial")
    done_longitude = fields.Float(string="Longitud comercial")


    # Distancia calculada

    distance_km = fields.Float(
        string="Distancia al punto (km)",
        compute="_compute_distance_km",
        store=True,
    )


    # Cálculo de distancia (Haversine)

    def _compute_distance_km(self):
        for event in self:
            if any(v is None for v in (
                event.planned_latitude,
                event.planned_longitude,
                event.done_latitude,
                event.done_longitude,
            )):
                event.distance_km = 0.0
                continue

            R = 6371.0  # Radio de la Tierra (km)

            lat1 = radians(event.planned_latitude)
            lon1 = radians(event.planned_longitude)
            lat2 = radians(event.done_latitude)
            lon2 = radians(event.done_longitude)

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            event.distance_km = R * c


    #  Geo localizar dirección de la reunión (botón)

    def action_geocode_planned_location(self):
        self.ensure_one()

        if not self.location:
            raise UserError("La reunión no tiene una dirección definida.")

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": self.location,
                "format": "jsonv2",
                "limit": 1,
            },
            headers={
                "User-Agent": "calendar_event_geo/1.0"
            },
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        if not data:
            raise UserError(
                "No se pudieron obtener coordenadas para la dirección indicada."
            )

        # Guardar coordenadas
        self.planned_latitude = float(data[0]["lat"])
        self.planned_longitude = float(data[0]["lon"])

        lat = self.planned_latitude
        lng = self.planned_longitude
        map_url = f"https://www.google.com/maps?q={lat},{lng}"

        html = Markup(
            "<b>📍 Ubicación planificada de la reunión</b><br/>"
            "Latitud: <code>%s</code><br/>"
            "Longitud: <code>%s</code><br/>"
            "<a href='%s' target='_blank'>🗺 Ver en Google Maps</a>"
        ) % (lat, lng, map_url)

        self.message_post(
            body=html,
            subtype_xmlid="mail.mt_note",
        )


    #  Geo localizar desde modal de actividad

    def action_activity_geolocate(self):
        self.ensure_one()

        if self.planned_latitude is None or self.planned_longitude is None:
            raise UserError(
                "Primero debes geolocalizar la dirección de la reunión."
            )

        lat = self.planned_latitude
        lng = self.planned_longitude
        map_url = f"https://www.google.com/maps?q={lat},{lng}"

        html = Markup(
            "<b>📍 Geolocalización desde actividad</b><br/>"
            "Latitud: <code>%s</code><br/>"
            "Longitud: <code>%s</code><br/>"
            "<a href='%s' target='_blank'>🗺 Ver en Google Maps</a>"
        ) % (lat, lng, map_url)

        self.message_post(
            body=html,
            subtype_xmlid="mail.mt_note",
        )


    # Bloquear cierre + publicar geo del comercial

    def write(self, vals):
        closing = "active" in vals and vals.get("active") is False

        res = super().write(vals)

        if closing:
            for event in self:

                # Reunión online → no validar
                if event.location == "Reunión en línea":
                    continue

                # Sin ubicación planificada → no validar
                if event.planned_latitude is None or event.planned_longitude is None:
                    continue

                #  Sin geolocalización del comercial
                if event.done_latitude is None or event.done_longitude is None:
                    raise UserError(
                        "No puedes cerrar la reunión si no has obtenido "
                        "tu geolocalización."
                    )

                #  Demasiado lejos
                if event.distance_km > 1:
                    raise UserError(
                        "No estás lo suficientemente cerca del punto "
                        "de la reunión.\n\n"
                        f"Distancia actual: {event.distance_km:.2f} km"
                    )

                lat = event.done_latitude
                lng = event.done_longitude
                map_url = f"https://www.google.com/maps?q={lat},{lng}"

                html = Markup(
                    f"""
                    <b>📍 Ubicación planificada de la reunión</b><br/>
                    Latitud: <code>{lat}</code><br/>
                    Longitud: <code>{lng}</code><br/>
                    <a href="{map_url}" target="_blank">🗺 Ver en Google Maps</a>
                    """
                )% (lat, lng, event.distance_km, map_url)

                event.message_post(
                    body=html,
                    subtype_xmlid="mail.mt_note",
                )

        return res