from odoo import models, fields


class SaesProviderPreviewWizard(models.TransientModel):
    _name = "saes.provider.preview.wizard"
    _description = "Preview RAW Proveedores"

    preview_text = fields.Text(
        string="Vista previa (datos crudos)",
        readonly=True
    )
