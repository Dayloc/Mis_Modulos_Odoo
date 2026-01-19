from odoo import models, fields

class SaesSaleInvoiceLineTableOption(models.TransientModel):
    _name = "saes.sale.invoice.line.table.option"
    _description = "Tabla candidata líneas factura de venta"

    name = fields.Char(string="Tabla", required=True)
    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade"
    )
