from odoo import fields, models
from odoo import api, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    """
    Hereda de 'product.template' para añadir una nueva opción al campo 'type'.
    """
    _inherit = 'product.template'

 
    type = fields.Selection(
        selection_add=[('ad_space', 'Superficie de Exhibición')],
        ondelete={'ad_space': 'set default'}
    )

    @api.model
    def _user_is_comercial(self):
        return self.env.user.has_group('mp_site.group_comerciales')

    def write(self, vals):
        if 'list_price' in vals and self._user_is_comercial():
            raise UserError(("No tienes permiso para cambiar el precio del producto."))
        return super().write(vals)