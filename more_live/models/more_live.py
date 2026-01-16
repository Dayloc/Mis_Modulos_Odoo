from odoo import models, api, fields
from datetime import timedelta


class MoreLiveConfigParams(models.AbstractModel):
    _name = "more_live.config.params"
    _description = "More Live Config Params"

    @api.model
    def update_config_params(self):
        icp = self.env["ir.config_parameter"].sudo()

        key = "database.create_date"

        # tomar la fecha actual del sistema (servidor)
        today = fields.Date.today()

        # restar 1 día → "ayer"
        new_date = today - timedelta(days=1)

        # guardar como string YYYY-MM-DD
        icp.set_param(key, fields.Date.to_string(new_date))
