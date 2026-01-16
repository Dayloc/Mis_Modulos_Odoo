from odoo import models, fields

class ReporteMin(models.Model):
    _name = 'reporte.min'
    _description = 'Modelo de ejemplo para reporte'

    name = fields.Char(string="Título", required=True)
    description = fields.Text(string="Descripción")
