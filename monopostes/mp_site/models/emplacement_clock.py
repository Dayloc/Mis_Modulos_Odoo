from odoo import models, fields

class EmplacementClock(models.Model):
    _name = 'emplacement.clock'
    _description = 'Emplacement Clock'

    name = fields.Char(string='Nombre', required=True)
    automatic = fields.Boolean(string='Automático', default=False)
