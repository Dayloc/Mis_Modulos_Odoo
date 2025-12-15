from odoo import models, fields,api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    linea_id = fields.Many2one('contact.linea', string="Línea", ondelete="restrict" )

    description_ids = fields.Many2many('contact.tag', string="Etiquetas" )


class ContactLinea(models.Model):
    _name = 'contact.linea'
    _description = 'Línea de Contacto'

    name = fields.Char(required=True)


class ContactTag(models.Model):
    _name = 'contact.tag'
    _description = 'Etiqueta de Contacto'

    name = fields.Char(required=True)
