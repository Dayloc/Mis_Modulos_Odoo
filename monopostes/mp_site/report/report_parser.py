from odoo import models, api

class ReportSaleOrderBaja(models.AbstractModel):
    _name = 'report.mp_site.report_sale_order_baja'
    _description = 'Informe Bajas Tramitadas'

    @api.model
    def _get_report_values(self, docids, data=None):
        orders = self.env['sale.order'].search([
            ('subscription_state', '=', '3_progress'),
            ('baja_tramitada', '=', True)
        ])

        return {
            'doc_ids': orders.ids,
            'doc_model': 'sale.order',
            'docs': orders,
        }
