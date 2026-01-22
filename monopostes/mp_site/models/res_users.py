from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_admin_monoposte = fields.Boolean(
        string="Administrador de Emplazamientos",
        default=True,
        compute='_compute_admin_monoposte',
        inverse='_inverse_admin_monoposte'
    )

    def _compute_admin_monoposte(self):
        group = self.env.ref('mp_site.group_admin_monoposte')
        for user in self:
            user.is_admin_monoposte = group in user.groups_id

    def _inverse_admin_monoposte(self):
        group = self.env.ref('mp_site.group_admin_monoposte')
        for user in self:
            if user.is_admin_monoposte:
                user.groups_id = [(4, group.id)]
            else:
                user.groups_id = [(3, group.id)]

    is_comerciales_monoposte = fields.Boolean(
        string="Comerciales de Monoposte",
        compute='_compute_comerciales_monoposte',
        inverse='_inverse_comerciales_monoposte'
    )

    def _compute_comerciales_monoposte(self):
        group = self.env.ref('mp_site.group_comerciales_monoposte')
        for user in self:
            user.is_comerciales_monoposte = group in user.groups_id

    def _inverse_comerciales_monoposte(self):
        group = self.env.ref('mp_site.group_comerciales_monoposte')
        for user in self:
            if user.is_comerciales_monoposte:
                user.groups_id = [(4, group.id)]
            else:
                user.groups_id = [(3, group.id)]
