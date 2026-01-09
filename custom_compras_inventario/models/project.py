from odoo import models, fields, api


class Project(models.Model):
    _inherit = "project.project"

    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Moneda",
        readonly=True,
        store=True,
    )

    stock_move_ids = fields.One2many(
        "stock.move",
        "proyecto_id",
        string="Gastos del proyecto",
        domain=[
            ("state", "=", "done"),
            ("purchase_line_id", "!=", False),
            ("location_dest_id.usage", "=", "internal"),
        ],
    )

    total_gastado = fields.Monetary(
        compute="_compute_total_gastado",
        currency_field="currency_id",
        store=False,
    )

    def _get_right_panel_data(self):
        data = super()._get_right_panel_data()

        StockMove = self.env["stock.move"]

        moves = StockMove.search([
            ("proyecto_id", "=", self.id),
            ("state", "=", "done"),
        ])

        total = sum(moves.mapped("costo_total"))

        if total:
            data["panel_purchase_cost"] = {
                "total": total,
                "currency_id": self.company_id.currency_id.id,
            }

        return data
    def get_total_gastos(self):
        self.ensure_one()
        return self.total_gastado

    @api.depends("stock_move_ids.costo_total")
    def _compute_total_gastado(self):
        for project in self:
            project.total_gastado = sum(
                project.stock_move_ids.mapped("costo_total")
            )
