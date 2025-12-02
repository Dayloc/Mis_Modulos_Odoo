from odoo import models, fields,api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    tiene_licencia = fields.Boolean("Tiene Licencia 📃")
    es_vip = fields.Boolean("Cliente VIP 👑")

    vip_badge_html = fields.Html("VIP Badge", compute="_compute_vip_badge")

    @api.depends('es_vip')
    def _compute_vip_badge(self):
            for rec in self:
                if rec.es_vip:
                    rec.vip_badge_html = """
                       <img src="/web/image/630"
                         style="width:80px; height:75px; margin-left:10px;"
                         alt="VIP"/>
                    """
                else:
                    rec.vip_badge_html = ""