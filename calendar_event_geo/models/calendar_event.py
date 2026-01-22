from odoo import models, fields, api
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

    show_regeocode_button = fields.Boolean(
        compute="_compute_show_regeocode_button",
        store=False,
    )

    def _compute_show_regeocode_button(self):
        for event in self:
            event.show_regeocode_button = bool(event.location)


    distance_km = fields.Float(
        string="Distancia al punto (km)",
        compute="_compute_distance_km",
        store=True,
    )


    @api.depends(
        "planned_latitude",
        "planned_longitude",
        "done_latitude",
        "done_longitude",
    )
    def _compute_distance_km(self):
        for event in self:
            if not all([
                event.planned_latitude,
                event.planned_longitude,
                event.done_latitude,
                event.done_longitude,
            ]):
                event.distance_km = 0.0
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


    def action_geocode_planned_location(self):
        self.ensure_one()

        if not self.location:
            raise UserError("La reunión no tiene una dirección definida.")

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": self.location,
                "format": "json",
                "limit": 1,
            },
            headers={"User-Agent": "Odoo-Calendar-Geo/1.0"},
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        if not data:
            raise UserError(
                "No se pudieron obtener coordenadas para la dirección indicada."
            )

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

        self.message_post(body=html, subtype_xmlid="mail.mt_note")


    @api.onchange("location")
    def _onchange_location_geocode(self):
        if not self.location:
            self.planned_latitude = False
            self.planned_longitude = False
            return

        try:
            res = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": self.location, "format": "json", "limit": 1},
                headers={"User-Agent": "Odoo-GeoValidation/1.0"},
                timeout=5,
            ).json()

            if not res:
                raise UserError("No se pudo geolocalizar la dirección.")

            self.planned_latitude = float(res[0]["lat"])
            self.planned_longitude = float(res[0]["lon"])

        except Exception:
            raise UserError("Error al geolocalizar la dirección.")
