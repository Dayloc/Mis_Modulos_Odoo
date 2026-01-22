# -*- coding: utf-8 -*-
from odoo import models, fields, _

class MpAdSpaceHistory(models.Model):
    _name = 'mp.ad.space.history'
    _description = 'Historial de Presupuestos de Espacios Publicitarios'
    _rec_name = 'sale_order_id'
    _order = 'create_date desc'

    ad_space_id = fields.Many2one('mp.site.ad.space', string='Espacio Publicitario', required=True, ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string='Presupuesto', required=True, ondelete='cascade')