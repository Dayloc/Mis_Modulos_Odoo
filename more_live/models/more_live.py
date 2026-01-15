from odoo import models, api, fields
from datetime import timedelta


class MoreLiveConfigParams(models.AbstractModel):
    _name = "more_live.config.params"
    _description = "More Live Config Params"

    @api.model
    def update_config_params(self):
        icp = self.env["ir.config_parameter"].sudo()

        key = "database.create_date"

        # leer valor actual
        value = icp.get_param(key)

        if value:
            # convertir string a date
            current_date = fields.Date.from_string(value)
        else:
            # Si no existe, usar fecha de hoy
            current_date = fields.Date.today()

        # sumar 1 día
        new_date = current_date - timedelta(days=1)

        # guardar como string YYYY-MM-DD
        icp.set_param(key, fields.Date.to_string(new_date))
