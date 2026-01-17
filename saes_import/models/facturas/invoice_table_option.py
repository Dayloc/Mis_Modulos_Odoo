from odoo import models, fields

class InvoiceTableOption(models.TransientModel):
    _name = "saes.invoice.table.option"
    _description = "Tabla candidata de facturas"

    name = fields.Char(string="Tabla", required=True)
    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade"
    )
