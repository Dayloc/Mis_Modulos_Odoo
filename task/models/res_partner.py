from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_coach = fields.Boolean(string="Es Entrenador")
    is_athlete = fields.Boolean(string="Es Atleta")
