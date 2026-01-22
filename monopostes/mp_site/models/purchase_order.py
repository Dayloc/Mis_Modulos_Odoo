from odoo import fields, models, api
import base64


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    intercambio_emplazamiento = fields.Boolean(
        string='Intercambio de emplazamiento',
        help='Activa esta opción para registrar una ubicación específica.'
    )
    ubicacion = fields.Char(
        string='Ubicación',
        help='Ubicación asociada al intercambio de emplazamiento.'
    )
    emplacement_text = fields.Char(string='Emplazamiento')
    kilometro = fields.Char(string='Kilómetro')
    municipio = fields.Char(string='Municipio')

    commission_agent_id = fields.Many2one(
        'res.partner',
        string='Comisionista',
        domain=[('is_company', '=', False)],
        help='Persona encargada de la comisión de esta compra.'
    )

    def action_rfq_send(self):
        res = super().action_rfq_send()

        ctx = res.get('context', {})
        active_ids = ctx.get('default_res_ids', [])
        active_id = active_ids[0] if active_ids else None

        po = self.browse(active_id)
        if not po:
            return res

        if po.intercambio_emplazamiento:
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                'mp_custom_reports.action_report_exchange_custom', [po.id]
            )

            attachment = self.env['ir.attachment'].create({
                'name': f'Propuesta_Intercambio_{po.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'purchase.order',
                'res_id': po.id,
                'mimetype': 'application/pdf',
            })

            if 'default_attachment_ids' in ctx and ctx['default_attachment_ids']:
                ctx['default_attachment_ids'].append(attachment.id)
            else:
                ctx['default_attachment_ids'] = [attachment.id]

            res['context'] = ctx

        return res
