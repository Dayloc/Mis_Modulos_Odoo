from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    emplacement_id = fields.Many2one(
        comodel_name="mp.site.emplacement",
        string="Emplazamiento",
        help="Emplazamiento asociado. Al seleccionarlo, se asignará el Inmueble AEAT correspondiente a las líneas."
    )