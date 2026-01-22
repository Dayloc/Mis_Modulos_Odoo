from odoo import models, fields, api

class DefineEmplacementWizard(models.TransientModel):
    _name = 'define.emplacement'
    _description = 'Asistente para definir información del emplazamiento'

    purchase_order_id = fields.Many2one('purchase.order', string='Orden de Compra')
    emplacement_id = fields.Many2one('mp.site.emplacement', string='Emplazamiento', required=True)
    emplacement_name = fields.Char(string='Nombre del Emplazamiento', required=True)
    additional_notes = fields.Text('Notas Adicionales')
    number_of_spaces = fields.Integer('Número de espacios', required=True, default=1)
    type_of_ad = fields.Selection([('valla', 'Valla'), ('monopost', 'Monoposte')], default='monopost', string='Tipo de Publicidad', required=True)
    create_project = fields.Boolean('Crear Proyecto Asociado', default=True)
    new_project_name = fields.Char('Nombre del Proyecto')

    def apply_changes(self):
        self.ensure_one()
        self.emplacement_id.write({
            'name': self.emplacement_name,
            'location_notes': self.additional_notes,
            'commision': self.purchase_order_id.opportunity_id.expected_comission,
            # 'emplacement_type': 'billboard' if self.type_of_ad == 'valla' else 'monopost',
        })

        if self.type_of_ad == 'valla':
            self.emplacement_id.emplacement_type = 'billboard'
        else:
            self.emplacement_id.emplacement_type = 'monopost'

        ProductTemplate = self.env['product.template']
        base_product = ProductTemplate.search([
            ('name', '=', 'Base'),
            ('type', '=', 'ad_space')
        ], limit=1)

        for x in range(self.number_of_spaces):
            vals = {
                'name': f"{self.emplacement_id.name} - {x + 1}",
                'emplacement_id': self.emplacement_id.id,
                'state': 'out_of_service',
                'size_id' : self.env.ref('mp_site.ad_space_size_10_4x5').id if self.env.ref('mp_site.ad_space_size_10_4x5', raise_if_not_found=False) else None,
            }
            if base_product:
                vals['product_id'] = base_product.id
            
            self.env['mp.site.ad.space'].create(vals)

        if self.create_project:
            project_name = self.new_project_name or f"Proyecto {self.emplacement_id.name}"
            new_project = self.env['project.project'].create({
                'name': project_name,
                'allow_billable': True,
                'emplacements_ids': self.emplacement_id,
            })
            self.purchase_order_id.project_id = new_project.id
        
        return {'type': 'ir.actions.act_window_close'}