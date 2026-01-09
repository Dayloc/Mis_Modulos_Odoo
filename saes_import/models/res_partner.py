from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    saes_code = fields.Char(
        string="Código SAE",
        index=True
    )
