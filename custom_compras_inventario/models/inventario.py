from odoo import models, fields, api


class MovimientoStock(models.Model):
    _inherit = "stock.move"

    proyecto_id = fields.Many2one(
        "project.project",
        string="Proyecto",
        domain="[('active', '=', True)]",
    )

    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Moneda",
        readonly=True,
        store=True,
    )

    costo_total = fields.Monetary(
        string="Costo",
        compute="_compute_costo_total",
        currency_field="company_currency_id",
        store=True,
    )


    @api.depends("quantity", "price_unit", "state")
    def _compute_costo_total(self):
        for move in self:
            if move.state == "done":
                move.costo_total = move.quantity * move.price_unit
            else:
                move.costo_total = 0.0


    @api.model_create_multi
    def create(self, vals_list):
        PurchaseLine = self.env["purchase.order.line"]

        for vals in vals_list:
            purchase_line_id = vals.get("purchase_line_id")
            if purchase_line_id and not vals.get("proyecto_id"):
                purchase_line = PurchaseLine.browse(purchase_line_id)
                if purchase_line.exists() and purchase_line.proyecto_id:
                    vals["proyecto_id"] = purchase_line.proyecto_id.id

        return super().create(vals_list)


    def write(self, vals):
        res = super().write(vals)

        if "purchase_line_id" in vals and not vals.get("proyecto_id"):
            for move in self:
                if move.purchase_line_id and move.purchase_line_id.proyecto_id:
                    move.proyecto_id = move.purchase_line_id.proyecto_id.id

        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    proyecto_id = fields.Many2one(
        related="move_id.proyecto_id",
        comodel_name="project.project",
        string="Proyecto",
        store=True,
        readonly=True,
    )
