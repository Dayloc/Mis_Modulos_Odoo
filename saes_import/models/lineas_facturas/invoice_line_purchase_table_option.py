from odoo import models, fields

class SaesPurchaseInvoiceLineTableOption(models.TransientModel):
    _name = "saes.purchase.invoice.line.table.option"
    _description = "Tabla candidata líneas factura de compra"

    name = fields.Char(string="Tabla", required=True)
    config_id = fields.Many2one(
        "saes.import.config",
        ondelete="cascade"
    )