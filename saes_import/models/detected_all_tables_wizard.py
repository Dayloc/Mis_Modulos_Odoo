from odoo import models, fields

class SaesDetectedTablesWizard(models.TransientModel):
    _name = "saes.detected.tables.wizard"
    _description = "Tablas detectadas"

    table_ids = fields.One2many(
        "saes.detected.table",
        "wizard_id",
        string="Tablas"
    )
