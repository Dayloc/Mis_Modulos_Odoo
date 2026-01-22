from odoo import models, fields, api

class SaleOrderProjectSelectionWizard(models.TransientModel):
    _name = 'sale.order.project.selection.wizard'
    _description = 'Seleccionar Proyecto para Orden de Venta'

    sale_order_id = fields.Many2one('sale.order', required=True)
    project_id = fields.Many2one('project.project', required=True)
    emplacement_id = fields.Many2one('product.product')
    selected_ad_space_id = fields.Many2one('mp.site.ad.space')

    def action_confirm_with_project(self):
        self.ensure_one()
        self.sale_order_id.project_id = self.project_id
        self.sale_order_id.ad_space_id = self.selected_ad_space_id
        return self.sale_order_id.action_confirm()
