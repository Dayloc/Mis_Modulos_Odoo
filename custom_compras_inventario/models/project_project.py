from odoo import models, api

class ProjectProject(models.Model):
    _inherit = "project.project"

    @api.model
    def get_purchase_expenses(self, project_id):
        moves = self.env["stock.move"].search([
            ("proyecto_id", "=", project_id),
        ])

        lines = []
        total = 0.0

        for move in moves:
            line_total = move.costo_total or (
                move.product_uom_qty * move.price_unit
            )

            total += line_total

            lines.append({
                "document": move.reference,
                "product": move.product_id.display_name,
                "qty": move.product_uom_qty,
                "price_unit": move.price_unit,
                "line_total": line_total,
            })

        return {
            "lines": lines,
            "total": total,
        }
