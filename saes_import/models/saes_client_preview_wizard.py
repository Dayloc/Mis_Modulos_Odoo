from odoo import models, fields
from odoo.exceptions import UserError


class SaesClientPreviewWizard(models.TransientModel):
    _name = "saes.client.preview.wizard"
    _description = "Preview de clientes SAE"

    preview_text = fields.Text(string="Vista previa", readonly=True)


