from odoo import models, fields, api

class SaesInvoicePreviewWizard(models.TransientModel):
    _name = "saes.invoice.preview.wizard"
    _description = "Preview de facturas"

    preview_html = fields.Html(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        html = self.env.context.get("preview_html")
        if html:
            res["preview_html"] = html
        return res
