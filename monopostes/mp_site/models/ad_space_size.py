from odoo import models, fields, api

class AdSpaceSize(models.Model):
    _name = 'ad.space.size'
    _description = 'Ad Space Size'

    width = fields.Float(string='Ancho', required=True)
    height = fields.Float(string='Alto', required=True)
    area = fields.Float(string='Área', compute='_compute_area', store=True)
    name = fields.Char(string='Nombre', compute='_compute_name', store=True)
    ad_space_ids = fields.One2many('mp.site.ad.space', 'size_id', string='Ad Spaces')

    @api.depends('width', 'height')
    def _compute_area(self):
        for record in self:
            if record.width and record.height:
                record.area = record.width * record.height
            else:
                record.area = 0

    @api.depends('width', 'height', 'area')
    def _compute_name(self):
        for record in self:
            if record.width and record.height:
                record.name = f"{record.width}x{record.height} ({record.area})"
            else:
                record.name = "Undefined"

class AdSpaceShaft(models.Model):
    _name = 'ad.space.shaft'
    _description = 'Ad Space Shaft'

    height = fields.Float(string='Alto')
    name = fields.Char(string='Nombre')

