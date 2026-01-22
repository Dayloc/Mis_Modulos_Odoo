from odoo import fields, models, api
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    opportunity_id = fields.Many2one(
        'mp.opportunity',
        string='Oportunidad Relacionada',
        copy=False
    )

    def action_open_opportunity(self):
        self.ensure_one()

        if not self.opportunity_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Oportunidad',
            'view_mode': 'form',
            'res_model': 'mp.opportunity',
            'res_id': self.opportunity_id.id,
    }

    def action_create_invoice(self):
        res = super(PurchaseOrder, self).action_create_invoice()
        return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        
        if self.opportunity_id: 
            self.opportunity_id.hired_state = 'formalizado'
            emplacement_name = f"{self.opportunity_id.name if self.opportunity_id else 'Sin Oportunidad'}"
            
            try:
                new_emplacement = self.env['mp.site.emplacement'].create({
                    'name': emplacement_name,
                    'emplacement_type': 'billboard', 
                    'property_type': 'rent',
                    'state': 'unavailable',
                    'location_notes': self.opportunity_id.Maps_link,
                })
            except Exception as e:
                raise UserError(f"Error al crear el emplazamiento: {e}. Asegúrate de que 'mp.site.emplacement' existe y los campos obligatorios están definidos.")

            if self.opportunity_id:
                self.opportunity_id.emplacement_id = new_emplacement.id
                self.opportunity_id.emplacement_id.commercial_id = self.opportunity_id.commercial.id


            return {
                'name': 'Definir Emplazamiento',
                'type': 'ir.actions.act_window',
                'res_model': 'define.emplacement',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_emplacement_id': new_emplacement.id,
                    'default_purchase_order_id': self.id,
                }   
            }

        return res