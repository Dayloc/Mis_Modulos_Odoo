# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MpSiteEmplacement(models.Model):
    _name = 'mp.site.emplacement'
    _description = 'Emplazamiento de Valla/Monoposte'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True)
    
    ad_space_ids = fields.One2many('mp.site.ad.space', 'emplacement_id', string='Espacios Publicitarios Asociados')
    
    active = fields.Boolean(string='Activo', default=True)

    project_id = fields.Many2one('project.project', string="Proyecto Asociado", ondelete='restrict',help="Proyecto de Odoo asociado a este Emplazamiento.")

    ubication = fields.Char(string='Ubicación General')
    
    city = fields.Char(string='Población')
    
    state_id = fields.Many2one("res.country.state", string='Provincia', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    
    country_id = fields.Many2one('res.country', string='País', ondelete='restrict')
    
    location_notes = fields.Text(string='Notas de Ubicación')

    license = fields.Boolean(string='Licencia', default=False)

    shaft = fields.Many2one('ad.space.shaft', string='Fuste')

    emplacement_type = fields.Selection([('billboard', 'Valla'),('monopost', 'Monoposte'),('bipost', 'Biposte'),('exchange','Intercambio'),], string='Tipo de Emplazamiento', required=True, default='billboard')

    # property_type = fields.Selection([('rent', 'Alquiler'), ('exchange', 'Intercambio'),('proposal', 'Propuesta (No Formalizada)'),('license', 'Licencia'),('own', 'Propiedad'),], string='Tipo de Propiedad', required=True, default='proposal')

    owner_id = fields.Many2one('res.partner', string='Propietario del Emplazamiento', help="Contacto del propietario en caso de intercambio, propuesta o licencia.")

    lighting_type = fields.Selection([('manual', 'Manual'),('automatic', 'Automático'),('none', 'Ninguno'),], string='Tipo de Iluminación', default='none')
    
    lighting_notes = fields.Text(string='Notas de Iluminación')
    
    last_lighting_check = fields.Date(string='Última Revisión de Iluminación')

    number_of_panels = fields.Char(string='Número de Paneles')

    commercial_id = fields.Many2one('res.users', string='Comercial', domain="[('share', '=', False)]", help="Usuario encargado de la comercialización del emplazamiento.")

    commision = fields.Float(string='Comisión (%)', default=0.0)

    # state = fields.Selection([('unavailable', 'De Baja'),('available', 'Disponible'),('available_exchange', 'Disponible por Intercambio'),('renewal_pending', 'Renovación Pendiente'),('in_negotiation', 'En Negociación'),], string='Estado del Emplazamiento', default='in_negotiation', tracking=True)

    leds = fields.Boolean(string='LEDs', default=False)

    plate_date = fields.Date(string='Fecha Placa')

    registration_details = fields.Text(string='Detalles Registrales')

    installation_date = fields.Date(string='Fecha de Instalación')

    check_date = fields.Date(string='Fecha Última Revisión')

    check_done = fields.Boolean(string='Revisión Realizada')

    observation = fields.Text(string='Observaciones')

    clock_id = fields.Many2one('emplacement.clock', string='Reloj')

    ref_catastral = fields.Char(string='Referencia Catastral')

    dismantled_date = fields.Date(string='Fecha de Desmontado :')

    # Technical Specifications
# BOOLS
    celosia = fields.Boolean(string='Celosía', default=False)
    moldura = fields.Boolean(string='Moldura', default=False)
    celula = fields.Boolean(string='Célula Fotoeléctrica', default=False)
    emplacement_dismantled=fields.Boolean(string="Emplazamiento desmontado", default=False)
# CHARS
    tubo_torretas = fields.Char(string='Tubo Torretas')
    placa_anclaje = fields.Char(string='Placa Anclaje')
    numero_garrotas = fields.Char(string='Nº Garrotas')
    zapata_cimentacion = fields.Char(string='Zapata Cimentación')
    tramo_1 = fields.Char(string='Tramo 1')
    tramo_2 = fields.Char(string='Tramo 2')
    tramo_3 = fields.Char(string='Tramo 3')
    tramo_4 = fields.Char(string='Tramo 4')
    placa_inferior = fields.Char(string='Placa Inferior')
    placa_superior = fields.Char(string='Placa Superior')
    cartelas_inferiores = fields.Char(string='Cartelas Inferiores')
    cartelas_superiores = fields.Char(string='Cartelas Superiores')
    bridas = fields.Char(string='Bridas')
    barra_vigas = fields.Char(string='Barra/Vigas')
    torretas = fields.Char(string='Torretas')
    siluetas = fields.Char(string='Siluetas')
    numero_piezas_torreta = fields.Char(string='Nº Piezas Torreta')
# MANY2ONE
    focus_number_id = fields.Many2one('mp.emplacement.focus.number', string='Nº Focos')
    tower_height_id = fields.Many2one('mp.emplacement.tower.height', string='Altura Torretas')
    concrete_id = fields.Many2one('mp.emplacement.concrete', string='Hormigón')
    ground_height_id = fields.Many2one('mp.emplacement.ground.height', string='Altura Suelo')
    dismantled_reason_id = fields.Many2one('mp.site.dismantled.reason',string='Motivo :')

    #AEAT MOD180 INTEGRATION
    codigo_via = fields.Char(string='Código Vía')
    tipo_via = fields.Char(string='Tipo Vía')
    tipo_numero_via = fields.Char(string='Tipo Número Vía')
    numero_via = fields.Char(string='Número Vía')
    numero_via2 = fields.Char(string='Número Vía 2')
    escalera = fields.Char(string='Escalera')
    piso = fields.Char(string='Piso')
    puerta = fields.Char(string='Puerta')
    letra = fields.Char(string='Letra')
    codigo_postal = fields.Char(string='Código Postal')
    codigo_municipio = fields.Char(string='Código Municipio')
    codigo_provincia = fields.Char(string='Código Provincia')
    clave_situacion = fields.Char(string='Clave Situación')
    localidad = fields.Char(string='Localidad')
    municipio = fields.Char(string='Municipio')

    
    @api.model_create_multi
    def create(self, vals_list):
        # Odoo 17+ can pass a dict or a list of dicts
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        records = super().create(vals_list)
        for rec in records:
            rec.create_project()
        return records


    def create_project(self):
        Project = self.env['project.project']
        for record in self:
            if not record.project_id:
                project = Project.create({
                    'name': record.name,
                    'emplacements_ids': [(4, record.id)],
                    'allow_billable': True,
                })
                record.project_id = project.id


    def action_open_project(self):
        self.ensure_one()
        if self.project_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.project',
                'view_mode': 'form',
                'res_id': self.project_id.id,
                'target': 'current',
            }
        else:
            # Opción: redirigir a la lista vacía de proyectos o mostrar un mensaje
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.project',
                'view_mode': 'list,form',
                'target': 'current',
            }

    def fix_sale_order(self):
        SaleOrderLine = self.env['sale.order.line']

        for emplacement in self.search([]):
            for ad_space in emplacement.ad_space_ids:
                if ad_space.name:
                    # Buscar líneas de pedido que contengan el nombre del ad_space en la descripción
                    matching_lines = SaleOrderLine.search([
                        ('name', 'ilike', ad_space.name)
                    ])
                    for line in matching_lines:
                        order = line.order_id
                        if ad_space not in order.ad_space_id:
                            order.ad_space_id = [(4, ad_space.id)]