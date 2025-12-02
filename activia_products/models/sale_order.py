from odoo import models
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for order in self:
            cliente = order.partner_id

            #  Validar productos peligrosos o exclusivos
            for line in order.order_line:
                tipo = line.product_id.product_tmpl_id.tipo_producto
                if tipo in ('peligroso', 'exclusivo') and not cliente.tiene_licencia:
                    raise UserError(
                        f"No se puede confirmar el pedido.\n"
                        f"El producto '{line.product_id.display_name}' es {tipo} "
                        f"y el cliente '{cliente.display_name}' NO tiene licencia."
                    )


        res = super().action_confirm()

        #  Marcar como VIP si supera 5000
        for order in self:
            if order.amount_total > 5000:
                order.partner_id.es_vip = True

        return res
