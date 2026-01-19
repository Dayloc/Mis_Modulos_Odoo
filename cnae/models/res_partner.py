from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    cnae_id = fields.Many2one(
        'cnae.cnae',
        string='CNAE'
    )
    cnae_code = fields.Char(
        related="cnae_id.code",
        store=True,
        readonly=True
    )
