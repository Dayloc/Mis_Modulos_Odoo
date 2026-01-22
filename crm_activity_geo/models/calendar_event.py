from odoo import models, fields, _
from odoo.exceptions import UserError
from math import radians, sin, cos, sqrt, atan2
from markupsafe import Markup
import requests


class CalendarEvent(models.Model):
    _inherit = "calendar.event"


    planned_latitude = fields.Float(string="Latitud reunión")
    planned_longitude = fields.Float(string="Longitud reunión")

    done_latitude = fields.Float(string="Latitud comercial")
    done_longitude = fields.Float(string="Longitud comercial")

    distance_km = fields.Float(
        string="Distancia al punto (km)",
        compute="_compute_distance_km",
        store=True,
    )


    def _compute_distance_km(self):
        for event in self:
            if not all([
                event.planned_latitude,
                event.planned_longitude,
                event.done_latitude,
                event.done_longitude,
            ]):
                event.distance_km = False
                continue

            R = 6371.0

            lat1 = radians(event.planned_latitude)
            lon1 = radians(event.planned_longitude)
            lat2 = radians(event.done_latitude)
            lon2 = radians(event.done_longitude)

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            event.distance_km = R * c


    def _check_meeting_close_constraints(self):
        self.ensure_one()

        # Reunión online → no validar
        if self.location == "Reunión en línea":
            return

        # Sin ubicación planificada → no validar
        if not self.planned_latitude or not self.planned_longitude:
            return

        # Sin geolocalización
        if not self.done_latitude or not self.done_longitude:
            raise UserError(
                _("No puedes cerrar la reunión sin obtener tu geolocalización.")
            )

        # Sin distancia calculada
        if not self.distance_km:
            raise UserError(_("No se pudo calcular la distancia a la reunión."))

        # Demasiado lejos
        if self.distance_km > 1:
            raise UserError(
                _("No estás lo suficientemente cerca del punto.\n\n"
                  "Distancia actual: %.2f km") % self.distance_km
            )


    def _post_done_location_message(self):
        self.ensure_one()

        lat = self.done_latitude
        lng = self.done_longitude
        map_url = f"https://www.google.com/maps?q={lat},{lng}"

        html = Markup(f"""
            <b>📍 Ubicación real del comercial</b><br/>
            Latitud: <code>{lat}</code><br/>
            Longitud: <code>{lng}</code><br/>
            <a href="{map_url}" target="_blank">🗺 Ver en Google Maps</a>
        """)

        self.message_post(
            body=html,
            subtype_xmlid="mail.mt_note",
        )


    def write(self, vals):
        closing = "active" in vals and vals.get("active") is False

        if closing:
            for event in self:
                event._check_meeting_close_constraints()
                event._post_done_location_message()

        return super().write(vals)


    def action_geocode_planned_location(self):
        self.ensure_one()

        if not self.location:
            raise UserError(_("La reunión no tiene una dirección definida."))

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": self.location,
                "format": "jsonv2",
                "limit": 1,
            },
            headers={"User-Agent": "calendar_event_geo/1.0"},
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        if not data:
            raise UserError(_("No se pudieron obtener coordenadas."))

        self.planned_latitude = float(data[0]["lat"])
        self.planned_longitude = float(data[0]["lon"])

        lat = self.planned_latitude
        lng = self.planned_longitude
        map_url = f"https://www.google.com/maps?q={lat},{lng}"

        html = Markup(f"""
            <b>📍 Ubicación planificada de la reunión</b><br/>
            Latitud: <code>{lat}</code><br/>
            Longitud: <code>{lng}</code><br/>
            <a href="{map_url}" target="_blank">🗺 Ver en Google Maps</a>
        """)

        self.message_post(body=html, subtype_xmlid="mail.mt_note")
