from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tipo_producto = fields.Selection([
        ('normal', 'Normal'),
        ('peligroso', 'Peligroso'),
        ('exclusivo', 'Exclusivo'),
    ], string="Tipo de Producto", default='normal')
