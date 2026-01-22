# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MpBenefitReportWizard(models.TransientModel):
    _name = 'mp.benefit.report.wizard'
    _description = 'Asistente de Reporte de Suscripciones Activas'


    def action_generate_report(self):
        def is_lighting_line(line):
            name_match = 'iluminaci' in (line.name or '').lower()
            product_match = 'iluminaci' in (line.product_id.name or '').lower()
            code_match = (line.product_id.default_code or '') == 'LIGHT-SRV'
            return name_match or product_match or code_match

        def get_signed_amount(move_line):
            # Si es factura Rectificativa (out_refund), restamos; si es Factura (out_invoice), sumamos
            sign = -1 if move_line.move_id.move_type == 'out_refund' else 1
            return move_line.price_subtotal * sign

        self.ensure_one()
        
        # Limpiar tabla de reporte
        self.env['mp.benefit.report.line'].search([]).unlink()

        lines_to_create = []
        # CONTROL DE DUPLICADOS: Guardamos los IDs de líneas ya usadas
        global_processed_line_ids = set()


        # ==============================================================================
        # 1. CASOS CON ESPACIO DEFINIDO (Tus casos 2 y 3)
        #    "Buscamos la sale order, buscamos su espacio y luego miramos si hay iluminacion"
        # ==============================================================================
        ad_spaces = self.env['mp.site.ad.space'].search([])

        for space in ad_spaces:
            if not space.name:
                continue

            space_name = space.name.strip()
            rent_income = 0.0
            lighting_income = 0.0
            found_order_id = False

            orders = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('subscription_state', '=', '3_progress'),
                ('order_line.name', 'ilike', space_name)
            ])

            for order in orders:
                if not found_order_id:
                    found_order_id = order.id

                for line in order.order_line:
                    
                    if line.id in global_processed_line_ids:
                        continue

                    line_name_clean = (line.name or '').lower()
                    
                    if space_name.lower() in line_name_clean and not is_lighting_line(line):
                        rent_income += line.price_subtotal

                    elif is_lighting_line(line):
                        lighting_income += line.price_subtotal
                        global_processed_line_ids.add(line.id)

            if rent_income != 0 or lighting_income != 0:
                lines_to_create.append({
                    'ad_space_id': space.id,
                    'emplacement_id': space.emplacement_id.id,
                    'state_id': space.emplacement_id.state_id.id if space.emplacement_id.state_id else False,
                    'sale_order_id': found_order_id,
                    'amount_rent': rent_income,
                    'amount_lighting': lighting_income,
                    'total_amount': rent_income + lighting_income,
                })
        
        emplacements = self.env['mp.site.emplacement'].search([('project_id', '!=', False)])

        for emp in emplacements:
            lighting_income = 0.0
            found_order_id = False

            orders = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('subscription_state', '=', '3_progress'),
                ('project_id.name', '=', emp.name),
                ('order_line.name', 'ilike', 'iluminaci') 
            ])

            for order in orders:
                for line in order.order_line:
                    if line.id in global_processed_line_ids:
                        continue

                    # Si es iluminación y está libre
                    if is_lighting_line(line):
                        lighting_income += line.price_subtotal
                        global_processed_line_ids.add(line.id)
                        
                        if not found_order_id:
                            found_order_id = order.id

            if lighting_income != 0:
                lines_to_create.append({
                    'ad_space_id': False, # Sin espacio
                    'emplacement_id': emp.id,
                    'state_id': emp.state_id.id if emp.state_id else False,
                    'sale_order_id': found_order_id,
                    'amount_rent': 0.0,
                    'amount_lighting': lighting_income,
                    'total_amount': lighting_income,
                })

        # ==============================================================================
        # 1. FACTURACION
        # ==============================================================================            
        ad_spaces = self.env['mp.site.ad.space'].search([])
        global_processed_line_ids = set()

        for space in ad_spaces:
            if not space.name:
                continue

            space_name = space.name.strip()
            
            # 1. BUSCAR LA CUENTA ANALÍTICA QUE SE LLAME IGUAL AL EMPLAZAMIENTO
            # Buscamos coincidencias exactas o parciales según prefieras. 
            # Aquí busco coincidencia exacta de nombre para mayor precisión.
            analytic_account = self.env['account.analytic.account'].search([
                ('name', '=', space.emplacement_id.name)
            ], limit=1)

            # Si no hay analítica con ese nombre, pasamos al siguiente espacio
            if not analytic_account:
                continue
            
            # Acumuladores temporales
            current_space_rent = 0.0
            current_space_lighting = 0.0
            
            # 2. BUSCAR FACTURAS PAGADAS
            # Nota: Quitamos el filtro 'invoice_line_ids.name' del search principal 
            # porque ahora filtraremos por Analítica en el bucle.
            moves = self.env['account.move'].search([
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['paid', 'in_payment']), 
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                # Opcional: Para optimizar, podríamos filtrar solo las que tengan líneas con esa analítica
                # pero depende de la versión de Odoo (si es v16 con JSON es difícil hacerlo en el search).
            ])

            for move in moves:
                for line in move.invoice_line_ids:
                    # Evitar duplicados globales
                    if line.id in global_processed_line_ids:
                        continue
                    
                    # Ignorar secciones y notas
                    if line.display_type in ('line_section', 'line_note'):
                        continue

                    # 3. VERIFICAR SI LA LÍNEA PERTENECE A LA ANALÍTICA DEL EMPLAZAMIENTO
                    is_analytic_match = False
                    
                    # Opción A: Odoo 16+ (analytic_distribution es un JSON/Diccionario)
                    if hasattr(line, 'analytic_distribution') and line.analytic_distribution:
                        # El diccionario tiene formato {'id_cuenta': porcentaje} -> {'5': 100.0}
                        # Convertimos el ID de la cuenta encontrada a string para buscarlo en las claves
                        if str(analytic_account.id) in line.analytic_distribution:
                            is_analytic_match = True
                            
                    # Opción B: Odoo versiones anteriores (analytic_account_id es Many2one)
                    elif hasattr(line, 'analytic_account_id') and line.analytic_account_id:
                        if line.analytic_account_id.id == analytic_account.id:
                            is_analytic_match = True

                    # Si la analítica no coincide, saltamos esta línea
                    if not is_analytic_match:
                        continue

                    # --- Lógica de clasificación por Nombre de Producto ---
                    # Obtenemos el nombre completo (Producto + Descripción) y lo pasamos a mayúsculas
                    line_text = (line.name or '').upper()
                    # Si quieres ser más preciso, usa también el nombre del producto base:
                    if line.product_id:
                        line_text += " " + (line.product_id.name or '').upper()

                    amount = get_signed_amount(line)
                    matched_category = False

                    # A. Es Iluminación
                    if 'ILUMINACION' in line_text or 'ILUMINACIÓN' in line_text:
                        current_space_lighting += amount
                        matched_category = True
                    
                    # B. Es Alquiler Monopostes
                    elif 'ALQUILER MONOPOSTES' in line_text or 'Exhibición publicitaria' in line_text:
                        current_space_rent += amount
                        matched_category = True
                    
                    # Si encontró categoría, marcamos la línea como procesada
                    if matched_category:
                        global_processed_line_ids.add(line.id)


            # --- GENERAR LÍNEA RESUMEN POR ESPACIO ---
            if current_space_rent != 0 or current_space_lighting != 0:
                lines_to_create.append({
                    'ad_space_id': space.id,
                    'emplacement_id': space.emplacement_id.id,
                    'state_id': space.emplacement_id.state_id.id if space.emplacement_id.state_id else False,
                    'fact_amount_rent': current_space_rent,
                    'fact_amount_lighting': current_space_lighting,
                    'fact_total_amount': current_space_rent + current_space_lighting,
                })


        # Insertar datos en la tabla temporal
        if lines_to_create:
            self.env['mp.benefit.report.line'].create(lines_to_create)

        return {
            'name': 'Ingresos por Suscripciones (Desglosado)',
            'type': 'ir.actions.act_window',
            'res_model': 'mp.benefit.report.line',
            'view_mode': 'list,pivot,graph',
            'target': 'current',
            'context': {'search_default_group_by_emplacement': 1},
        }


class MpBenefitReportLine(models.TransientModel):
    _name = 'mp.benefit.report.line'
    _description = 'Línea de Reporte de Suscripciones'
    _order = 'emplacement_id, ad_space_id'

    ad_space_id = fields.Many2one('mp.site.ad.space', string='Espacio Publicitario', readonly=True)
    emplacement_id = fields.Many2one('mp.site.emplacement', string='Emplazamiento', readonly=True)
    state_id = fields.Many2one('res.country.state', string='Provincia', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Suscripción', readonly=True)
    
    amount_rent = fields.Float(string='Ingreso Recurrente Alquiler', readonly=True)
    amount_lighting = fields.Float(string='Ingreso Recurrente Iluminación', readonly=True)
    total_amount = fields.Float(string='Total Recurrente', readonly=True)

    fact_amount_rent = fields.Float(string='Facturado por Alquiler', readonly=True)
    fact_amount_lighting = fields.Float(string='Facturado por Iluminación', readonly=True)
    fact_total_amount = fields.Float(string='Total Facturado', readonly=True)