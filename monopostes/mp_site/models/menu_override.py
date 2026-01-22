from odoo import models, api

# Override to hide project menus for users in the 'Comerciales' group
class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _filter_visible_menus(self):
        menus = super()._filter_visible_menus()
        user = self.env.user
        group_comerciales = self.env.ref('mp_site.group_comerciales', raise_if_not_found=False)

        if group_comerciales and user.has_group('mp_site.group_comerciales'):
            project_menu_ids = [
                self.env.ref('project.menu_main_pm', raise_if_not_found=False),
                self.env.ref('project.menu_projects', raise_if_not_found=False),
                self.env.ref('project.menu_project_management', raise_if_not_found=False),
            ]
            project_menu_ids = [menu.id for menu in project_menu_ids if menu]
            return menus.filtered(lambda menu: menu.id not in project_menu_ids)
        return menus
