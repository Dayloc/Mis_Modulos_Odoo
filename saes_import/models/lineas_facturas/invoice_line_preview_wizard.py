from odoo import models, fields, api

class SaesInvoiceLinePreviewWizard(models.TransientModel):
    _name = "saes.invoice.line.preview.wizard"
    _description = "Preview líneas de factura"

    preview_html = fields.Html(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        html = self.env.context.get("preview_html")
        if html:
            res["preview_html"] = html
        return res
