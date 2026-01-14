from odoo import models, fields, api

class SaesProductPreviewWizard(models.TransientModel):
    _name = "product.preview.wizard"
    _description = "Preview de productos SAE"

    preview_html = fields.Html(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("preview_html"):
            res["preview_html"] = self.env.context["preview_html"]
        return res
