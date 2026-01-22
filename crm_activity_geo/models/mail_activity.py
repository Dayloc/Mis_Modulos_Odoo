from odoo import models, fields
from odoo.exceptions import UserError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    geo_latitude = fields.Float(string="Latitud")
    geo_longitude = fields.Float(string="Longitud")
    geo_address = fields.Char(string="Dirección")

    def action_done(self):
        for activity in self:
            # Solo actividades ligadas a reuniones
            if activity.res_model == "calendar.event" and activity.res_id:
                event = self.env["calendar.event"].browse(activity.res_id)

                # Copiar geolocalización de la actividad al evento
                if activity.geo_latitude and activity.geo_longitude:
                    event.write({
                        "done_latitude": activity.geo_latitude,
                        "done_longitude": activity.geo_longitude,
                    })

                # Validar reglas de cierre
                event._check_meeting_close_constraints()

                # Publicar ubicación
                event._post_done_location_message()

        return super().action_done()
