from odoo import models, fields

class MpSiteDismantledReason(models.Model):
    _name = 'mp.site.dismantled.reason'
    _description = 'Motivo de desmontaje de emplazamiento'
    _order = 'sequence, name'

    name = fields.Char(string='Motivo', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
