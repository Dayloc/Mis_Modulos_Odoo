# -*- coding: utf-8 -*-
from odoo import models, fields

class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    # Campos relacionados con la compañía
    street = fields.Char(related='company_id.street', readonly=True)
    zip = fields.Char(related='company_id.zip', readonly=True)
    city = fields.Char(related='company_id.city', readonly=True)
    country_id = fields.Many2one(related='company_id.country_id', readonly=True)
    company_registry = fields.Char(related='company_id.company_registry', readonly=True)
    state_id = fields.Many2one(related='company_id.state_id', readonly=True)
    phone = fields.Char(related='company_id.phone', readonly=True)
    email = fields.Char(related='company_id.email', readonly=True)