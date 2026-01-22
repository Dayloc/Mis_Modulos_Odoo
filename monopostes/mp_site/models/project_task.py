from odoo import models, fields

# Añadir campo Many2many para contactos en tareas de proyecto
class ProjectTask(models.Model):
    _inherit = 'project.task'

    partner_ids = fields.Many2many('res.partner', string='Contactos')