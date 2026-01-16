from odoo import _,api, fields, models

class Task(models.Model):
    _name = 'task'
    _description = 'Sample Model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    date = fields.Date(string='Date')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    partner_id = fields.Many2one(
        'res.partner',
        string='Responsable',
        help='Selecciona un cliente/contacto'
    )
    
    def button_action(self):
        pass
    
    @api.model_create_multi
    def create(self, vals):
        """Create records using provided values."""
        res = super().create(vals)
        return res
    
    def write(self, vals):
        """Write records using provided values."""
        res = super().write(vals)
        return res
    
    def unlink(self):
        """Delete records"""
        print("Deleting records")
        return super().unlink()

    def print_task_report(self):
        return self.env.ref('task.action_report_task').report_action(self)
