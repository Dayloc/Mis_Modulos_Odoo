from odoo import api, fields, models


class RecipientRecord(models.Model):
    _name = "recipient.record"
    _description = "Recipient Record"

    report_id = fields.Many2one(
        "l10n.es.aeat.mod180.report", string="AEAT 180 Report", ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", string="Empresa")
    l10n_es_aeat_real_estate_id = fields.Many2one(
        "l10n.es.aeat.real.estate", string="Información catastral"
    )
    sign = fields.Selection(
        selection=[(" ", "Positivo"), ("N", "Negativo")],
        string="Signo Base Retenciones",
    )
    retentions_base = fields.Float(
        string="Base retenciones e ingresos a cuenta", digits=(13, 2)
    )
    retentions_fee = fields.Float(
        string="Retenciones e ingresos a cuenta", digits=(13, 2)
    )
    retentions_percentage = fields.Float(string="% Retención", digits=(2, 2))
    accrual_year = fields.Integer(string="Ejercicio Devengo")
    base_move_line_ids = fields.Many2many(
        "account.move.line",
        "reg_perceptor_base_move_line_rel",
        "reg_perceptor_id",
        "move_line_id",
        string="Apuntes contable de base",
    )
    
    # MODIFICADO: Se elimina el compute y el store=True temporalmente para evitar el error de dependencia
    representative_vat = fields.Char(
        string="Representative VAT",
        size=9,
        help="VAT number of the legal representative of the recipient",
        # compute="_compute_representative_vat",  # <--- COMENTADO POR ERROR EN ODOO 18
        # store=True,                             # <--- COMENTADO
        readonly=False,
    )

    emplacement_id = fields.Many2one(
        "mp.site.emplacement", 
        string="Emplazamiento"
    )

    # MODIFICADO: Comentamos toda la función porque depende de un campo que ya no existe en la v18
    # @api.depends("l10n_es_aeat_real_estate_id.representative_vat", "partner_id.vat")
    # @api.onchange("l10n_es_aeat_real_estate_id", "partner_id")
    # def _compute_representative_vat(self):
    #     for record in self:
    #         # El campo representative_vat ya no existe en l10n.es.aeat.real_estate en v18
    #         # if (
    #         #     record.partner_id.vat
    #         #     != record.l10n_es_aeat_real_estate_id.representative_vat
    #         # ):
    #         #     record.representative_vat = (
    #         #         record.l10n_es_aeat_real_estate_id.representative_vat
    #         #     )
    #         # else:
    #         #     record.representative_vat = ""
    #         
    #         # Esta llamada también es peligrosa si el método privado cambió en v18
    #         # record.l10n_es_aeat_real_estate_id._compute_real_estate_situation()
    #         pass

    def action_get_base_move_lines(self):
        res = self.env.ref("account.action_account_moves_all_a").read()[0]
        view = self.env.ref("l10n_es_aeat.view_move_line_tree")
        res["views"] = [(view.id, "list")]
        res["domain"] = [("id", "in", self.base_move_line_ids.ids)]
        return res