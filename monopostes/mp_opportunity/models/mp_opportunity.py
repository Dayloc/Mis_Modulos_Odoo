# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MPOpportunity(models.Model):
    _name = 'mp.opportunity'
    _description = 'Oportunidades de Mantenimiento y Proyectos'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Referencia de la Oportunidad',
        required=True,
    )

    active = fields.Boolean(string='Activo',default=True)

    expected_license = fields.Boolean(
        string='Licencia prevista',
        default=False
    )

    expected_comission = fields.Float(
        string='Comisión prevista (%)',
        compute='_compute_expected_comission',
        store=True
    )

    date = fields.Date(
        string='Fecha',
        default=fields.Date.today()
    )

    quarter = fields.Selection(
        [
            ('q1', 'Q1'),
            ('q2', 'Q2'),
            ('q3', 'Q3'),
            ('q4', 'Q4'),
        ],
        string='Trimestre',
        compute='_compute_quarter',
        store=True
    )

    emplacement_id = fields.Many2one(
        'mp.site.emplacement',
        string='Emplazamiento',
        ondelete='set null'
    )

    city = fields.Char(string='Localidad')

    province = fields.Char( string='Provincia')

    owner = fields.Many2one(
        'res.partner',
        string='Propietario',
        required=True,
    )

    commercial = fields.Many2one(
        'res.users',
        string='Comercial',
        default=lambda self: self.env.user
    )

    @api.model
    def _group_expand_states(self, states, domain):
        return ['borrador', 'propuesto', 'formalizado', 'desestimado']

    hired_state = fields.Selection(
        selection=[
            ('borrador', 'Borrador'),
            ('propuesto', 'Propuesto'),
            ('formalizado', 'Formalizado'),
            ('desestimado', 'Desestimado'),
        ],
        string='Estado',
        required=True,
        copy=False,
        tracking=True,
        default='borrador',
        group_expand='_group_expand_states',
    )

    observations = fields.Text(
        string='Observaciones'
    )

    amount = fields.Float(
        string='Importe',
        digits=(10, 2)
    )

    Maps_link = fields.Char( string='Enlace Google Maps')

    # --- Modelos asociados ---

    purchase_order_ids = fields.One2many(
        'purchase.order',
        'opportunity_id',
        string='Órdenes de Compra'
    )
    
        ## Contadores de modelos asociados

    purchase_count = fields.Integer(string="Compras",  default=0)

    def action_get_purchases(self):
        self.ensure_one()
        purchases = self.env['purchase.order'].search([('opportunity_id', '=', self.id)])
        if len(purchases) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Compra',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'res_id': purchases.id,
                'context': {'create': False},
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Compras',
                'view_mode': 'list,form',
                'res_model': 'purchase.order',
                'domain': [('opportunity_id', '=', self.id)],
                'context': {'create': False},
            }

    def action_get_proyects(self):
        self.ensure_one()
        projects = self.env['project.project'].search([('purchase_order_ids.opportunity_id', '=', self.id)])
        if len(projects) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Proyecto',
                'view_mode': 'form',
                'res_model': 'project.project',
                'res_id': projects.id,
                'context': {'create': False},
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Proyectos',
                'view_mode': 'list,form',
                'res_model': 'project.project',
                'domain': [('purchase_order_ids.opportunity_id', '=', self.id)],
                'context': {'create': False},
            }
        
    def action_get_emplacement(self):
        self.ensure_one()
        Emplacement = self.env['mp.site.emplacement']
        emplacements = Emplacement.search([('project_id.purchase_order_ids.opportunity_id', '=', self.id)])

        if len(emplacements) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Emplazamiento',
                'view_mode': 'form',
                'res_model': 'mp.site.emplacement',
                'res_id': emplacements.id,
                'context': {'create': False},
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Emplazamientos',
                'view_mode': 'list,form',
                'res_model': 'mp.site.emplacement',
                'domain': [('project_id.purchase_order_ids.opportunity_id', '=', self.id)],
                'context': {'create': False},
            }

    
    def action_get_sales(self):
        self.ensure_one()
        SaleOrder = self.env['sale.order']
        sales = SaleOrder.search([('project_id.purchase_order_ids.opportunity_id', '=', self.id)])

        if len(sales) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Venta',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': sales.id,
                'context': {'create': False},
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Ventas',
                'view_mode': 'list,form',
                'res_model': 'sale.order',
                'domain': [('project_id.purchase_order_ids.opportunity_id', '=', self.id)],
                'context': {'create': False},
            }


    # --- Funciones y métodos ---

    @api.depends('date')
    def _compute_quarter(self):
        for record in self:
            if record.date:
                month = record.date.month
                if 1 <= month <= 3:
                    record.quarter = 'q1'
                elif 4 <= month <= 6:
                    record.quarter = 'q2'
                elif 7 <= month <= 9:
                    record.quarter = 'q3'
                else:
                    record.quarter = 'q4'
            else:
                record.quarter = False

    def action_create_purchase_order(self):
        """
        Crea un nuevo presupuesto de compra y redirige al usuario a su formulario.
        Añade una línea de producto "Nuevo Emplazamiento" con el importe y la descripción de la oportunidad.
        """
        self.ensure_one()

        product_obj = self.env['product.product']
        emplacement_product = product_obj.search([('name', '=', 'Nuevo Emplazamiento')], limit=1)
        vendor = self.owner

        if not emplacement_product:
            emplacement_product = product_obj.create({
                'name': 'Nuevo Emplazamiento',
                'type': 'service',
                'list_price': 0.0,
                'standard_price': 0.0,
            })

        purchase_order = self.env['purchase.order'].create({
            'partner_id': vendor.id if vendor else False,
            'origin': self.name, 
            'opportunity_id': self.id,
            # 'user_id' : self.commercial.user_id,
            'order_line': [(0, 0, { # Añade la línea de producto
                'product_id': emplacement_product.id,
                'name': self.emplacement_id or 'Descripción del emplazamiento', # Descripción de la línea
                'product_qty': 1.0, # Cantidad por defecto
                'price_unit': self.amount, # Precio unitario es el importe de la oportunidad
                'date_planned': fields.Date.today(), # Fecha planificada
            })]
        })

        self.hired_state = 'propuesto'

        # Retorna una acción de ventana para abrir el formulario de la orden de compra recién creada
        return {
            'name': 'Nuevo Presupuesto de Compra',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id,
            'target': 'current',
            'context': {
                'default_partner_id': vendor.id if vendor else False,
                'default_origin': self.name,
                'default_opportunity_id': self.id,
                'default_order_line': [(0, 0, {
                    'product_id': emplacement_product.id,
                    'name': self.emplacement_id or 'Descripción del emplazamiento',
                    'product_qty': 1.0,
                    'price_unit': self.amount,
                })]
            }
        }
    

    @api.depends('amount', 'expected_license')
    def _compute_expected_comission(self):
        for record in self:
            comission = 0.0
            if record.amount >= 3000:
                comission += 1.0
            if record.expected_license:
                comission += 1.0
            record.expected_comission = min(comission, 2.0)

    def action_set_desestimado(self):
        for record in self:
            # Cambiar estado de la oportunidad
            record.hired_state = 'desestimado'
            
            # Cancelar órdenes de compra relacionadas
            for po in record.purchase_order_ids:
                if po.state not in ['cancel', 'done']:  # Solo cancelamos si no está ya cancelada o completada
                    po.button_cancel()  # Cancela la orden de compra
            
            # Vaciar la relación One2many en la oportunidad
            record.purchase_order_ids = False

    def action_set_borrador(self):
        for record in self:
            record.hired_state = 'borrador'


