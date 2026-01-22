import logging
import re  # <--- IMPORTANTE: Necesario para detectar el ID correctamente
from odoo import models, api

_logger = logging.getLogger(__name__)

class Mod180Handler(models.AbstractModel):
    _name = 'l10n.es.aeat.mod180.handler'
    _inherit = 'account.report.custom.handler'
    _description = 'Modelo 180 Handler'
    
    def _custom_line_postprocessor(self, report, options, lines):
            # 1. Ejecutar lógica original
            lines = super()._custom_line_postprocessor(report, options, lines)

            # 2. Localizar índices de las columnas dinámicamente
            # Usamos diccionarios para no liarnos con los índices numéricos
            col_indices = {}
            target_labels = ['nif', 'base', 'tax', 'percent_tax']
            
            for idx, col in enumerate(report.column_ids):
                if col.expression_label in target_labels:
                    col_indices[col.expression_label] = idx

            # Si falta alguna columna crítica, salimos para evitar errores
            if 'nif' not in col_indices:
                return lines

            # Pre-cargamos modelo
            Partner = self.env['res.partner']

            # 3. Recorrer líneas
            for line in lines:
                if not line.get('columns'):
                    continue
                
                # --- A. LÓGICA DEL NIF ---
                line_id_str = str(line.get('id'))
                match = re.search(r'~res\.partner~(\d+)', line_id_str)
                
                if match:
                    partner_id = int(match.group(1))
                    partner = Partner.browse(partner_id)
                    vat = partner.vat or '' 
                    
                    # Escribir NIF
                    idx_nif = col_indices['nif']
                    if len(line['columns']) > idx_nif:
                        line['columns'][idx_nif]['name'] = vat
                        line['columns'][idx_nif]['no_format'] = vat
                
                # --- B. LÓGICA DEL PORCENTAJE ---
                # Solo calculamos si tenemos las columnas necesarias (Base, Cuota y Destino %)
                if 'base' in col_indices and 'tax' in col_indices and 'percent_tax' in col_indices:
                    idx_base = col_indices['base']
                    idx_tax = col_indices['tax']
                    idx_pct = col_indices['percent_tax']

                    # Verificamos que la línea tiene longitud suficiente
                    if len(line['columns']) > max(idx_base, idx_tax, idx_pct):
                        
                        # Obtenemos valor numérico ('no_format' suele ser float o None)
                        base_val = line['columns'][idx_base].get('no_format') or 0.0
                        tax_val = line['columns'][idx_tax].get('no_format') or 0.0

                        percentage_str = "0,00 %" # Valor por defecto

                        if base_val != 0:
                            # Calculamos: (Cuota / Base) * 100
                            percent = (tax_val / base_val) * 100
                            # Formateamos a string español: 19.0 -> "19,00 %"
                            percentage_str = "{:.2f} %".format(percent).replace('.', ',')
                        
                        # Escribimos en la columna
                        line['columns'][idx_pct]['name'] = percentage_str
                        line['columns'][idx_pct]['no_format'] = (tax_val / base_val) * 100 if base_val else 0

            return lines