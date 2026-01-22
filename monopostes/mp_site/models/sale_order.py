# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ad_space_id = fields.Many2many('mp.site.ad.space', string='Advertising Space')
    ad_space_valid_ids = fields.Many2many(
        'mp.site.ad.space',
        string="Espacios válidos",
        compute='_compute_ad_space_valid_ids'
    )
    baja_tramitada = fields.Boolean(string='Baja tramitada', default=False)
    fecha_pedido = fields.Date(string='Fecha de pedido', default=fields.Date.context_today)
    has_emplacement_products = fields.Boolean(string="Contiene Productos 'Sitio'", compute='_compute_has_site_products', store=True)
    emplacement_sale_order = fields.Boolean(default=True, string="Venta de Emplazamiento")
    ad_space_warning = fields.Boolean(string='Advertencia por conflicto de espacio', compute='_compute_ad_space_warning')
    comisionista_venta_id = fields.Many2one('res.users', string='Comisionista de Venta')
    comisionista_emplazamiento_id = fields.Many2one('res.users', string='Comisionista de Emplazamiento')
    comision_venta = fields.Float(string='Comisión por venta(%)', default=0.0)
    comision_emplazamiento = fields.Float(string='Comisión por emplazamiento (%)', default=0.0)
    order_type = fields.Selection([('alquiler', 'Alquiler'), ('venta', 'Venta'), ('trabajo', 'Trabajo')], compute='_compute_order_type', string='Tipo de pedido')
    show_invoice_by_line_button = fields.Boolean(compute='_compute_show_invoice_by_line_button', store=False)

    @api.model
    def _get_bajas_tramitadas_en_progreso(self):
        return self.search([
            ('state', '=', '3_progress'),
            ('baja_tramitada', '=', True)
        ])

    def action_assign_billable_project_from_ad_space(self):
        for order in self:
            ad_space = order.ad_space_id
            if ad_space and ad_space.emplacement_id and ad_space.emplacement_id.project_id:
                order.project_id = ad_space.emplacement_id.project_id

    def action_reasign_ad_space(self):
        for order in self:
            found_spaces = self.env['mp.site.ad.space'].search([])
            
            for line in order.order_line:
                if not line.product_id or not line.name:
                    continue

                for space in found_spaces:
                    if space.name.strip().lower() in line.name.strip().lower():
                        order.write({'ad_space_id': [(4, space.id)]})

                        
    @api.depends('baja_tramitada')
    def _compute_ad_space_valid_ids(self):
        AdSpace = self.env['mp.site.ad.space']

        # 1. Obtener espacios disponibles
        available_spaces = AdSpace.search([('state', '=', 'available')])
        reserved_spaces = AdSpace.search([('state', '=', 'reserved')])

        # 2. Obtener espacios ocupados relacionados a sale.order con baja_tramitada = True
        orders_with_baja = self.env['sale.order'].search([('baja_tramitada', '=', True)])
        occupied_spaces = orders_with_baja.mapped('ad_space_id').filtered(lambda s: s.state == 'occupied')


        # 3. Combinar ambos
        valid_spaces = available_spaces | occupied_spaces | reserved_spaces

        for order in self:
            order.ad_space_valid_ids = valid_spaces

    def write(self, vals):
        res = super().write(vals)

        for order in self:
            # Procesar cambios en estado del pedido de venta
            new_order_state = vals.get('state', order.state)
            new_sub_state = vals.get('subscription_state', order.subscription_state)

            # 1. Manejo del estado del pedido
            if new_order_state:
                if new_order_state == 'sale':
                    order.ad_space_id.write({'state': 'occupied'})
                elif new_order_state == 'cancel':
                    order.ad_space_id.write({'state': 'available'})

            # 2. Manejo del churn (suscripción terminada)
            if new_sub_state == '6_churn' and order.ad_space_id:
                order.ad_space_id.write({'state': 'available'})

        return res

    @api.depends('order_line.product_id')
    def _compute_order_type(self):
        for order in self:
            order_type = 'venta'  # Valor por defecto

            for line in order.order_line:
                product = line.product_id
                if product.recurring_invoice:
                    order_type = 'alquiler'
                    break  # prioridad más alta
                elif product.type == 'service':
                    order_type = 'trabajo'
                    # no salimos aún, por si encontramos una de suscripción

            order.order_type = order_type

    @api.onchange('fecha_pedido')
    def _change_next_invoice_date(self):
            if self.fecha_pedido:
                self.next_invoice_date = self.fecha_pedido

    @api.depends('ad_space_id', 'fecha_pedido')
    def _compute_ad_space_warning(self):
        for order in self:
            order.ad_space_warning = False
        return

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.fecha_pedido:
            invoice_vals['invoice_date'] = self.fecha_pedido
        return invoice_vals

    @api.depends('order_line.product_id.product_tmpl_id.type')
    def _compute_has_site_products(self):
        for order in self:
            order.has_emplacement_products = any(line.product_id.type == 'emplacement' for line in order.order_line)

    def action_confirm(self):
        if self.has_emplacement_products and self.ad_space_id:
            self.ad_space_id.state = 'occupied'
            self.ad_space_id.usage_count += 1
            self.ad_space_id.current_advertiser_id = self.partner_id
            if self.ad_space_id.emplacement_id.commercial_id:
                self.user_id = self.ad_space_id.emplacement_id.commercial_id.id
        return super(SaleOrder, self).action_confirm()
    
    @api.onchange('ad_space_id')
    def _onchange_include_lights(self):
        if not self:
            return

        Product = self.env['product.product']
        SaleOrderLine = self.env['sale.order.line']

        # Buscar o crear el producto 'Iluminación'
        product_ilumination = Product.search([('name', '=', 'Iluminación')], limit=1)
        if not product_ilumination:
            product_ilumination = Product.create({
                'name': 'Iluminación',
                'type': 'service',
                'list_price': 50.0,
                'default_code': 'LIGHT-SRV',
                'sale_ok': True,
                'purchase_ok': False,
            })

        # Filtrar ad_spaces que tienen iluminación activa
        ad_spaces_with_light = self.ad_space_id.filtered(
            lambda ad_space: ad_space.emplacement_id and ad_space.emplacement_id.lighting_type not in (False, 'none', '')
        )

        # Crear nombres únicos por cada ad_space
        current_light_names = {f"Iluminación - {ad_space.name.strip()}" for ad_space in ad_spaces_with_light}

        # Filtrar líneas existentes del producto 'Iluminación'
        light_lines = self.order_line.filtered(lambda l: l.product_id.id == product_ilumination.id)

        # Eliminar líneas que ya no correspondan a ad_spaces con iluminación
        lines_to_remove = light_lines.filtered(lambda l: l.name.strip() not in current_light_names)
        if lines_to_remove:
            self.order_line -= lines_to_remove

        # Nombres de líneas existentes (para no duplicar)
        existing_light_names = {line.name.strip() for line in light_lines}

        # Crear nuevas líneas por cada ad_space con iluminación activa
        for ad_space in ad_spaces_with_light:
            line_name = f"Iluminación - {ad_space.name.strip()}"
            if line_name not in existing_light_names:
                self.order_line += SaleOrderLine.new({
                    'product_id': product_ilumination.id,
                    'name': line_name,
                    'product_uom_qty': 1,
                    'price_unit': product_ilumination.lst_price or 0.0,
                })


    @api.onchange('ad_space_id')
    def _onchange_include_decoration(self):
        product_deco = self.env['product.product'].search([('name', '=', 'Decoración en vinilo')], limit=1)
        if not product_deco:
            return

        # Agrupar espacios por área
        area_count_map = {}
        for ad_space in self.ad_space_id:
            area = ad_space.size_id.area
            if area:
                area_str = f"{area}m2"
                area_count_map[area_str] = area_count_map.get(area_str, 0) + 1

        # Crear un conjunto con nombres de áreas usados actualmente
        current_areas = set(area_count_map.keys())

        # Actualizar o crear líneas según el área
        for area_str, count in area_count_map.items():
            area_value = float(area_str.replace('m2', ''))
            price = product_deco.lst_price * area_value

            existing_line = self.order_line.filtered(
                lambda l: l.product_id.id == product_deco.id and l.name == area_str
            )
            if existing_line:
                existing_line.update({
                    'product_uom_qty': count,
                    'price_unit': price,
                })
            else:
                self.order_line += self.env['sale.order.line'].new({
                    'product_id': product_deco.id,
                    'name': area_str,
                    'product_uom_qty': count,
                    'price_unit': price,
                })

        # Eliminar líneas de decoración que ya no aplican
        decoration_lines = self.order_line.filtered(lambda l: l.product_id.id == product_deco.id)
        for line in decoration_lines:
            if line.name not in current_areas:
                self.order_line -= line

    @api.onchange('ad_space_id')
    def _onchange_ad_space_id(self):
        if not self:
            return
        SaleOrderLine = self.env['sale.order.line']

        product_monoposte = self.env['product.product'].search([('name', '=', 'ALQUILER MONOPOSTES')], limit=1)
        product_valla = self.env['product.product'].search([('name', '=', 'ALQUILER VALLAS')], limit=1)

        if not product_monoposte or not product_valla:
            raise UserError("Los productos 'ALQUILER MONOPOSTES' y 'ALQUILER VALLAS' deben existir en el sistema.")

        current_ad_space_names = {ad_space.name.strip() for ad_space in self.ad_space_id}

        rental_lines = self.order_line.filtered(
            lambda l: l.product_id.id in (product_monoposte.id, product_valla.id)
        )

        # Quitar líneas que ya no correspondan a espacios seleccionados
        lines_to_remove = rental_lines.filtered(
            lambda l: l.name.strip() not in current_ad_space_names
        )
        if lines_to_remove:
            self.order_line -= lines_to_remove

        existing_ad_space_names = {line.name.strip() for line in rental_lines}

        for ad_space in self.ad_space_id:
            name = ad_space.name.strip()

            if name not in existing_ad_space_names:

                # Determinar producto según prefijo
                if name.upper().startswith("MP"):
                    product = product_monoposte
                elif name.upper().startswith("V"):
                    product = product_valla
                else:
                    raise UserError(
                        f"El espacio '{name}' no empieza por MP ni V, no se puede asignar producto."
                    )

                new_line = SaleOrderLine.new({
                    'product_id': product.id,
                    'name': name,
                    'product_uom_qty': 1,
                    'price_unit': ad_space.product_id.lst_price or 0.0,
                })
                self.order_line += new_line


    @api.onchange('order_line')
    def _onchange_order_line(self):
        if not self:
            return

        # Productos válidos
        product_monoposte = self.env['product.product'].search([('name', '=', 'ALQUILER MONOPOSTES')], limit=1)
        product_valla = self.env['product.product'].search([('name', '=', 'ALQUILER VALLAS')], limit=1)

        valid_products = (product_monoposte + product_valla).ids

        if not valid_products:
            return

        # Nombres de líneas relacionadas con ad_spaces
        current_line_names = {
            line.name.strip()
            for line in self.order_line
            if line.product_id.id in valid_products and line.name
        }

        if not current_line_names:
            return

        # Mantener solo ad_spaces con coincidencia en nombre
        self.ad_space_id = self.ad_space_id.filtered(
            lambda ad: ad.name.strip() in current_line_names
        )

# Metodo para facturar por líneas
    def action_invoice_by_line(self):
        self.ensure_one()

        # Productos principales
        product_monoposte = self.env['product.product'].search([('name', '=', 'ALQUILER MONOPOSTES')], limit=1)
        product_valla = self.env['product.product'].search([('name', '=', 'ALQUILER VALLAS')], limit=1)

        if not product_monoposte or not product_valla:
            raise UserError("No se encontraron los productos 'ALQUILER MONOPOSTES' o 'ALQUILER VALLAS'.")

        # Productos secundarios
        product_light = self.env['product.product'].search([('name', '=', 'Iluminación')], limit=1)
        product_deco = self.env['product.product'].search([('name', '=', 'Decoración en vinilo')], limit=1)

        # ---------------------------------------------------------
        # LÍNEAS DE EMPLAZAMIENTO A FACTURAR
        # ---------------------------------------------------------
        emplacement_lines = self.order_line.filtered(
            lambda l: l.product_id.id in (product_monoposte.id, product_valla.id)
                    and l.qty_to_invoice > 0
        )

        if not emplacement_lines:
            raise UserError("No hay líneas de emplazamiento pendientes por facturar.")

        invoices = self.env['account.move']

        # Inicializar contador de EMP
        emp_counter = 1
        base_name = self.name.strip()

        # ---------------------------------------------------------
        # PROCESAR CADA ESPACIO
        # ---------------------------------------------------------
        for line in emplacement_lines:

            ad_space_name = line.name.strip()

            # Crear nombre del pedido temporal con contador: 2025-079-EMP-1, 2, 3...
            temp_name = f"{base_name}-EMP-{emp_counter}"
            emp_counter += 1

            # Crear pedido temporal
            temp_order = self.copy({
                'name': temp_name,
            })

            # Mantener solo la línea del espacio actual
            temp_order.order_line.filtered(
                lambda l: l.product_id.id != line.product_id.id or l.name != line.name
            ).unlink()

            # Sincronizar el ad_space correcto
            matching_ad_spaces = temp_order.ad_space_id.filtered(
                lambda ad: ad.name.strip() == ad_space_name
            )
            temp_order.ad_space_id = [(6, 0, matching_ad_spaces.ids)]

            # -----------------------------------------------------
            # AÑADIR ILUMINACIÓN SI EL ESPACIO LA TIENE
            # -----------------------------------------------------
            if (
                product_light
                and matching_ad_spaces
                and matching_ad_spaces.emplacement_id.lighting_type not in (False, 'none', '')
            ):
                temp_order.order_line += self.env['sale.order.line'].new({
                    'product_id': product_light.id,
                    'name': f"Iluminación - {ad_space_name}",
                    'product_uom_qty': 1,
                    'price_unit': product_light.lst_price,
                    'product_uom': product_light.uom_id.id,
                    'tax_id': [(6, 0, product_light.taxes_id.ids)],
                })

            # Confirmar pedido temporal
            temp_order.action_confirm()

            # Facturar
            if temp_order.invoice_status == 'sale':
                invoice = temp_order._create_invoices()
                if invoice:
                    invoices |= invoice

        # ---------------------------------------------------------
        # PROCESAR DECORACIÓN (TODAS JUNTAS) — sin cambios
        # ---------------------------------------------------------
        if product_deco:
            deco_lines = self.order_line.filtered(lambda l: l.product_id.id == product_deco.id)
        else:
            deco_lines = False

        if deco_lines:
            deco_order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'user_id': self.user_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'date_order': self.date_order,
                'origin': self.name,
                'name': f"{self.name}-DECOR",
            })

            for line in deco_lines:
                self.env['sale.order.line'].create({
                    'order_id': deco_order.id,
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'product_uom': line.product_uom.id,
                    'tax_id': [(6, 0, line.tax_id.ids)],
                })

            deco_order.action_confirm()
            if deco_order.invoice_status == 'sale':
                deco_invoice = deco_order._create_invoices()
                if deco_invoice:
                    invoices |= deco_invoice

        # ---------------------------------------------------------
        # CANCELAR PEDIDO ORIGINAL
        # ---------------------------------------------------------
        self._action_cancel()

        return

    @api.depends('state', 'ad_space_id', 'order_line.product_id')
    def _compute_show_invoice_by_line_button(self):
        for order in self:
            has_deco = any(line.product_id.name == 'Decoración' for line in order.order_line)
            order.show_invoice_by_line_button = (
                (order.state == 'sale' and len(order.ad_space_id) > 1) or
                (order.state == 'sale' and has_deco and len(order.ad_space_id) == 1)
            )

    def copy_project_analytic_to_lines(self):
            for sale in self:
                project = sale.project_id
                if not project:
                    _logger.warning("Venta %s no tiene proyecto asociado.", sale.name)
                    continue

                if not project.account_id:
                    _logger.warning("Proyecto %s no tiene cuenta analítica.", project.name)
                    continue

                account_id = project.account_id.id
                analytic_dist = {account_id: 100.0}  # 100% a la cuenta analítica

                for line in sale.order_line:
                    try:
                        line.write({'analytic_distribution': analytic_dist})
                    except Exception as e:
                        _logger.error(
                            "No se pudo asignar analítica a la línea %s de la venta %s: %s",
                            line.id, sale.name, e
                        )

                _logger.info(
                    "Distribución analítica del proyecto %s copiada a las líneas de venta %s",
                    project.name, sale.name
                )
            return True

    def action_quotation_send(self):
        res = super().action_quotation_send()

        for order in self:
            for ad_space in order.ad_space_id:
                # Evita duplicados si se envía varias veces
                existing = self.env['mp.ad.space.history'].search([
                    ('ad_space_id', '=', ad_space.id),
                    ('sale_order_id', '=', order.id)
                ], limit=1)

                if not existing:
                    self.env['mp.ad.space.history'].create({
                        'ad_space_id': ad_space.id,
                        'sale_order_id': order.id,
                    })

        return res

    def action_reconvertir_presupuesto(self):
        self.ensure_one()  # Solo un presupuesto a la vez

        Product = self.env['product.product']

        # Buscar productos de destino
        product_monoposte = Product.search([('name', '=', 'ALQUILER MONOPOSTES')], limit=1)
        product_valla = Product.search([('name', '=', 'ALQUILER VALLAS')], limit=1)

        if not product_monoposte or not product_valla:
            raise UserError(_("No se encontraron los productos 'ALQUILER MONOPOSTES' o 'ALQUILER VALLAS'."))

        # Crear el nuevo presupuesto copiando campos principales
        new_order = self.copy({
            'name': self.env['ir.sequence'].next_by_code('sale.order') or '/',
            'state': 'draft',
            'ad_space_id': [(6, 0, self.ad_space_id.ids)],
            'project_id': self.project_id.id,
        })

        # Limpiar líneas copiadas automáticamente
        new_order.order_line.unlink()

        # Copiar líneas
        for line in self.order_line:
            product = line.product_id

            # Revisar si es producto de exhibición publicitaria y reemplazar según el nombre
            if product.type in ('consu', 'service') and line.name:
                name_upper = line.name.strip().upper()
                if name_upper.startswith("MP-"):
                    product = product_monoposte
                elif name_upper.startswith("V-"):
                    product = product_valla

            # Crear la línea en el nuevo presupuesto
            self.env['sale.order.line'].create({
                'order_id': new_order.id,
                'product_id': product.id,
                'name': line.name,
                'product_uom_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'product_uom': line.product_uom.id,
                'tax_id': [(6, 0, line.tax_id.ids)],
            })

        if new_order.amount_total == self.amount_total:
            # Montos iguales: cancelamos la vieja y dejamos la nueva
            self._action_cancel()
            
            new_order.message_post_with_source(
                'mail.message_origin_link',
                render_values={'self': new_order, 'origin': self},  # nuevo → viejo
                subtype_xmlid='mail.mt_note',
            )

            # Abrir el nuevo presupuesto
            return {
                'name': _('Nuevo Presupuesto'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': new_order.id,
                'target': 'current',
            }
        else:
            # Montos diferentes: descartamos la nueva y mantenemos la vieja
            new_order.unlink()
            return {
                'warning': {
                    'title': _("Reconversion descartada"),
                    'message': _("El nuevo presupuesto tiene un total diferente al original. No se realizó la reconversión."),
                }
            }