# -*- coding: utf-8 -*-

from odoo import _,api, fields, models

class AccountComitionist(models.Model):
    _inherit = 'account.move'
    _description = 'Añadimos un campo comisionista para el reporte dee comisionista'

    
    comisionista = fields.Boolean(string='Comisión Pagada', help='Indica si pago la comisión de la factura')

    def action_marcar_comisionista_true(self):
        """Función para el botón: marca como True los registros seleccionados"""
        for record in self:
            record.comisionista = True
