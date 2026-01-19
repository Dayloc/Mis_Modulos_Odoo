import json
import os
from odoo import models, fields, api, SUPERUSER_ID


class Cnae(models.Model):
    _name = 'cnae.cnae'
    _description = 'CNAE'
    _order = 'code'

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código CNAE debe ser único.')
    ]

    def name_get(self):
        return [(r.id, f"{r.code} - {r.name}") for r in self]

    @api.model
    def init(self):
        module_path = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(module_path, 'data', 'cnae_2025.json')

        if not os.path.isfile(json_path):
            return

        with open(json_path, encoding='utf-8') as f:
            records = json.load(f)

        for item in records:
            code = item.get('code')
            name = item.get('name')

            if not code or not name:
                continue

            if not self.search([('code', '=', code)], limit=1):
                self.sudo().create({
                    'code': code,
                    'name': name,
                })
