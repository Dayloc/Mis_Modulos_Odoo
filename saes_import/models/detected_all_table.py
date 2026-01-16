from odoo import models, fields, api

class SaesDetectedTable(models.TransientModel):
    _name = "saes.detected.table"
    _description = "Tabla detectada"
    _order = "name asc"

    sequence = fields.Integer(
        string="#",
        compute="_compute_sequence",
        store=False
    )

    name = fields.Char(string="Tabla", required=True)

    wizard_id = fields.Many2one(
        "saes.detected.tables.wizard",
        ondelete="cascade"
    )

    @api.depends("wizard_id")
    def _compute_sequence(self):
        for wizard in self.mapped("wizard_id"):
            tables = wizard.table_ids.sorted(lambda r: r.name.lower())
            for idx, table in enumerate(tables, start=1):
                table.sequence = idx

    def name_get(self):
        result = []
        for rec in self:
            if rec.sequence:
                result.append((rec.id, f"{rec.sequence}. {rec.name}"))
            else:
                result.append((rec.id, rec.name))
        return result
