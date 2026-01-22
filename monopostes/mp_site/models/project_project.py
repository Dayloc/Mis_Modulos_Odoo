# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class Project(models.Model):
    _inherit = 'project.project'

    emplacements_ids = fields.One2many('mp.site.emplacement','project_id',string="Emplazamientos Asociadas")

    emplacement_count = fields.Integer(string='Emplazamientos',compute='_compute_emplacement_count',help="Número de emplazamientos asociados a este proyecto.")

    @api.depends('emplacements_ids')
    def _compute_emplacement_count(self):
        for record in self:
            record.emplacement_count = len(record.emplacements_ids)
            record.sale_order_count = len(record.sale_order_ids)

    def action_view_emplacements(self):
        self.ensure_one()
        action = self.env.ref('mp_site.mp_site_emplacement_action').read()[0]
        emplacements = self.emplacements_ids
        if len(emplacements) == 1:
            action['views'] = [(self.env.ref('mp_site.mp_site_emplacement_form_view').id, 'form')]
            action['res_id'] = emplacements.id
        else:
            action['domain'] = [('id', 'in', emplacements.ids)]
        return action