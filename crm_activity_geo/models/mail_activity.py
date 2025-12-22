from odoo import models, fields

class MailActivity(models.Model):
    _inherit = "mail.activity"

    geo_latitude = fields.Float(string="Latitud")
    geo_longitude = fields.Float(string="Longitud")
    geo_address = fields.Char(string="Dirección")
