from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrderProjectSelection(models.TransientModel):
    _name = 'sale.order.project.selection.wizard'
    _description = 'Wizard to select or create a project for a sale order'

    project_id = fields.Many2one('project.project', string='Existing Project')
    emplacement_id = fields.One2many(related='project_id.emplacements_ids', string='Associated Emplacements', readonly=True)
    selected_ad_space_id = fields.Many2one(
        'mp.site.ad.space', 
        string='Select Ad Space',
        domain="[('emplacement_id', '=', emplacement_id)]"
    )
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)

    def action_confirm_with_project(self):
        self.ensure_one()
        sale_order = self.sale_order_id

        if not self.selected_ad_space_id:
            raise UserError("Debes seleccionar un Espacio Publicitario para continuar.")

        # Nueva validación: Si hay un emplazamiento, se requiere un espacio publicitario.
        if self.emplacement_id and not self.selected_ad_space_id:
            raise UserError(("Debes seleccionar un Espacio Publicitario para continuar."))

        if self.project_id:
            # Opción 1: Vincular a un proyecto existente
            project = self.project_id
        else:
            # Opción 2: Crear un nuevo proyecto
            project_vals = {
                'name': f"{sale_order.partner_id.name} - {sale_order.name}",
                'sale_order_ids': [(4, sale_order.id)],
            }
            project = self.env['project.project'].create(project_vals)
            
        # Creamos el emplazamiento y lo vinculamos al proyecto
        emplacement_name = f"Emplazamiento para Venta: {sale_order.name}"
        new_emplacement = self.env['mp.site.emplacement'].create({
            'name': emplacement_name,
            'emplacement_type': 'billboard',
            'state': 'in_negotiation',
            'project_id': project.id,
        })

        # Actualizamos la orden de venta con el proyecto, el emplazamiento y el ad_space
        sale_order.write({
            'project_id': project.id,
            'ad_space_id': self.selected_ad_space_id.id,
        })
        
        # Confirmamos la venta
        sale_order.action_confirm()

        return {'type': 'ir.actions.act_window_close'}
