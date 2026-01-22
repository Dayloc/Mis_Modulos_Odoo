from odoo import models, api
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

# Evitar que los usuarios del grupo 'Comerciales' 
# puedan modificar el precio unitario en las líneas de pedido de venta
    @api.onchange('price_unit')
    def _onchange_price_unit_commercial(self):
        if self.env.user.has_group('mp_site.group_comerciales'):
            raise UserError("No tienes permiso para modificar el precio unitario.")
