from odoo import models, fields, _


class CrmLead(models.Model):
    _inherit = "crm.lead"

    meeting_latitude = fields.Float(string="Latitud reunión")
    meeting_longitude = fields.Float(string="Longitud reunión")

    geo_latitude = fields.Float(string="Latitud comercial", default=0.0)
    geo_longitude = fields.Float(string="Longitud comercial", default=0.0)

    def action_geolocalize_meeting(self):
        for lead in self:

            lat = lead.meeting_latitude
            lng = lead.meeting_longitude


            if not lat or not lng:
                continue

            url = f"https://www.google.com/maps?q={lat},{lng}"

            lead.message_post(
                body=_(
                    "<b>📍 Geolocalización de la reunión</b><br/>"
                    "Latitud: <code>%s</code><br/>"
                    "Longitud: <code>%s</code><br/>"
                    "<a href='%s' target='_blank'>🗺 Ver en Google Maps</a>"
                ) % (lat, lng, url),
                subtype_xmlid="mail.mt_note",
            )
