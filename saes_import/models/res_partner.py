from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    saes_code = fields.Char(
        string="Código SAGES",
        index=True
    )
    x_aux_account = fields.Char(
        string="Cuenta auxiliar / ID externo"
    )