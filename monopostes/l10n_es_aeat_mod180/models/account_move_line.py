from odoo import fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_es_aeat_real_estate_id = fields.Many2one(
        comodel_name="l10n.es.aeat.real.estate",
        string="Inmueble AEAT",
        help="Inmueble asociado para el cálculo del Modelo 180"
    )