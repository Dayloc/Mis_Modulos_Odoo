# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class MpSiteAdSpace(models.Model):
    _name = 'mp.site.ad.space'
    _description = 'Espacio Publicitario'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Identificador de Espacio Publicitario', required=True, copy=False, default='Nuevo')
    
    active = fields.Boolean(string='Activo', default=True)
    
    ad_space_history_ids = fields.One2many('mp.ad.space.history','ad_space_id',string='Historial de Presupuestos')
 
    campaign_id = fields.Many2one(
        'utm.campaign',
        string='Campaña',
        compute='_compute_new_campaign',
        store=True,
        readonly=True
    )

    commercialization_ease = fields.Selection([('easy', 'Fácil'),('normal', 'Normal'),('difficult', 'Difícil'),], string='Facilidad para Comercialización', default='normal')

    count_used = fields.Integer(string='Veces Presupuestado',compute='_compute_count_used',)
 
    current_advertiser_id = fields.Many2one('res.partner', string='Cliente', readonly=True)
 
    emplacement_id = fields.Many2one('mp.site.emplacement', string='Emplazamiento Asociado')

    emplacement_city = fields.Char(
        string='Población',
        related='emplacement_id.city',
        store=True,
        readonly=True
    )

    emplacement_state = fields.Many2one(
        'res.country.state',
        string='Provincia',
        related='emplacement_id.state_id',
        store=True,
        readonly=True
    )

    emplacement_lighting_type = fields.Selection(
        related='emplacement_id.lighting_type',
        string='Iluminación',
        store=True,
        readonly=True
    )

    fecha_fin_contrato = fields.Date(
        string='Fin del contrato',
        compute='_compute_fecha_fin_contrato',
        store=True,
        readonly=False
    )

    product_id = fields.Many2one('product.product', string='Tarifa', help="Producto de Odoo asociado a este espacio publicitario para gestión comercial.")

    size_id = fields.Many2one('ad.space.size', string='Tamaño')
    
    state = fields.Selection([('available', 'Disponible'),('offered', 'Ofertado'),('occupied', 'Ocupado'),('out_of_service', 'Fuera de Servicio Temporalmente'),('dismount','Desmontado'),('reserved','Reservado')], string='Estado del Espacio', default='available', tracking=True)
    
    ubication = fields.Char(string='Ubicación', related='emplacement_id.ubication', store=True)

    usage_count = fields.Integer(string='Número de Usos', default=0, help="Contador de veces que el espacio ha sido usado. Máximo 3 usos para limpieza.")

    way = fields.Char(string='Sentido')

    @api.depends('state')
    def _compute_new_campaign(self):
        for ad_space in self:
            ad_space.campaign_id = False
            if ad_space.state == 'occupied':
                # Buscar la sale.order más reciente que tenga este espacio
                order = self.env['sale.order'].search([
                    ('ad_space_id', 'in', ad_space.ids),
                    ('state', '=', 'sale'),
                    ('end_date', '!=', False),
                ], limit=1, order='end_date desc')

                if order:
                    ad_space.current_advertiser_id = order.partner_id.id
                    ad_space.campaign_id = order.campaign_id.id

    @api.depends('state')
    def _compute_fecha_fin_contrato(self):
        for ad_space in self:
            if not ad_space.fecha_fin_contrato:
                ad_space.fecha_fin_contrato = False

            if ad_space.state != 'occupied':
                continue

            ad_space.fecha_fin_contrato = False
            if ad_space.state == 'occupied':
                # Buscar la sale.order más reciente que tenga este espacio
                order = self.env['sale.order'].search([
                    ('ad_space_id', 'in', ad_space.ids),
                    ('baja_tramitada', '=', True),
                    ('state', '=', 'sale'),
                    ('end_date', '!=', False),
                ], limit=1, order='end_date desc')

                if order:
                    ad_space.fecha_fin_contrato = order.end_date

    @api.depends('ad_space_history_ids')
    def _compute_count_used(self):
        for record in self:
            record.count_used = len(record.ad_space_history_ids)

    def action_enable_ad_space(self):
        for record in self:
            record.state = 'available'
            record.usage_count += 1
            record.current_advertiser_id = None 
            if record.usage_count == 3:
                record.state = 'out_of_service'

    def calculate_availability(self):
        active_states = ['sale']  # Puedes ajustar esto según tu flujo de negocio
        SaleOrder = self.env['sale.order']

        for space in self:
            sale_orders = SaleOrder.search([
                ('ad_space_id', 'in', [space.id]),
                ('state', 'in', active_states)
            ])

            if sale_orders:
                space.state = 'occupied'
            else:
                space.state = 'available'