from odoo import models, fields

class SaesInvoiceLineTableOption(models.TransientModel):
    _name = "saes.invoice.line.table.option"
    _description = "Tabla candidata de líneas de factura"

    name = fields.Char(string="Tabla", required=True)

    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade",
    )
