from odoo import models, fields

class SaesDetectedTable(models.TransientModel):
    _name = "saes.detected.table"
    _description = "Tabla detectada"

    name = fields.Char(string="Tabla", required=True)
    wizard_id = fields.Many2one(
        "saes.detected.tables.wizard",
        ondelete="cascade"
    )

