from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class L10nEsAeatMod180Report(models.Model):
    _description = "AEAT 180 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod180.report"
    _aeat_number = "180"
    _period_yearly = True
    _period_quarterly = False
    _period_monthly = False

    casilla_01 = fields.Integer(
        string="[01] # Recipients",
        readonly=True,
        compute="_compute_casilla_01",
        help="Number of recipients",
    )
    casilla_02 = fields.Float(
        string="[02] Base retenciones e ingresos a cuenta",
        readonly=True,
        compute="_compute_casilla_02",
        store=True,
    )
    casilla_03 = fields.Float(
        string="[03] Retenciones e ingresos a cuenta",
        readonly=True,
        compute="_compute_casilla_03",
        help="Amount of retentions",
        store=True,
    )

    sign = fields.Selection(
        selection=[(" ", "Positivo"), ("N", "Negativo")],
        string="Signo Casilla 03",
        compute="_compute_casilla_03",
        store=True,
    )
    casilla_04 = fields.Float(
        string="[04] Fees to compensate",
        readonly=True,
        help="Fee to compensate for prior results with same subject, "
        "fiscal year and period (in which his statement was to return "
        "and compensation back option was chosen).",
        store=True,
    )
    casilla_05 = fields.Float(
        string="[05] Result",
        readonly=True,
        compute="_compute_casilla_05",
        help="Result: ([03] - [04])",
        store=True,
    )
    tipo_declaracion = fields.Selection(
        selection=[
            ("I", "To enter"),
            ("U", "Direct debit"),
            ("G", "To enter on CCT"),
            ("N", "To return"),
        ],
        string="Result type",
        default="N",
        readonly=True,
        required=True,
    )
    tipo_declaracion_positiva = fields.Selection(
        selection=[("I", "To enter"), ("U", "Direct debit"), ("G", "To enter on CCT")],
        string="Result type (positive)",
        compute="_compute_tipo_declaracion",
        inverse="_inverse_tipo_declaracion",
        store=True,
    )
    tipo_declaracion_negativa = fields.Selection(
        selection=[("N", "To return")],
        string="Result type (negative)",
        compute="_compute_tipo_declaracion",
        inverse="_inverse_tipo_declaracion",
        store=True,
    )

    recipient_record_ids = fields.One2many(
        comodel_name="recipient.record",
        inverse_name="report_id",
        string="Registros de perceptores",
    )

    @api.depends("tipo_declaracion")
    def _compute_tipo_declaracion(self):
        for rec in self:
            if rec.tipo_declaracion == "N":
                rec.tipo_declaracion_negativa = rec.tipo_declaracion
                rec.tipo_declaracion_positiva = False
            else:
                rec.tipo_declaracion_positiva = rec.tipo_declaracion
                rec.tipo_declaracion_negativa = False

    def _inverse_tipo_declaracion(self):
        for rec in self:
            if rec.casilla_05 > 0.0:
                rec.tipo_declaracion = rec.tipo_declaracion_positiva
            else:
                rec.tipo_declaracion = rec.tipo_declaracion_negativa

    @api.constrains("tipo_declaracion")
    def _check_tipo_declaracion(self):
        for rec in self:
            if rec.casilla_05 <= 0.0 and rec.tipo_declaracion != "N":
                raise ValidationError(
                    _(
                        "The result of the declaration is negative. "
                        "You should select another Result type"
                    )
                )
            elif rec.casilla_05 > 0.0 and rec.tipo_declaracion == "N":
                raise ValidationError(
                    _(
                        "The result of the declaration is positive. "
                        "You should select another Result type"
                    )
                )

    @api.depends("tax_line_ids", "tax_line_ids.move_line_ids")
    def _compute_casilla_01(self):
        casillas = (2, 3)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas
            )
            report.casilla_01 = len(
                tax_lines.mapped("move_line_ids").mapped("partner_id")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_02(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 2)
            report.casilla_02 = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_03(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 3)
            report.casilla_03 = sum(tax_lines.mapped("amount"))
            if report.casilla_03 < 0:
                report.sign = "N"
            else:
                report.sign = " "

    @api.depends("casilla_03", "casilla_04")
    def _compute_casilla_05(self):
        for report in self:
            report.casilla_05 = report.casilla_03 - report.casilla_04

    def button_confirm(self):
        """Check bank account completion."""
        msg = ""
        for report in self.filtered(lambda x: not x.partner_bank_id):
            if report.tipo_declaracion in ("U", "N"):
                msg = (
                    _("Select an account for making the charge")
                    if report.tipo_declaracion == "U"
                    else _("Select an account for receiving the money")
                )
        if msg:
            raise UserError(msg)
        return super().button_confirm()

    def button_cancel(self):
        res = super().button_cancel()
        return res

    def button_recover(self):
        res = super().button_recover()
        return res

    def calculate(self):
        res = super().calculate()
        self._crear_registros_percetores()
        for rec in self:
            if rec.casilla_05 <= 0.0:
                rec.tipo_declaracion = "N"
            else:
                rec.tipo_declaracion = "I"
        return res

    def _crear_registros_percetores(self):
            _logger.info(">>> INICIO _crear_registros_percetores (OPTIMIZADO) <<<")
            self.recipient_record_ids.unlink()

            # 1. Buscar Mapa de impuestos
            tax_code_map = self.env["l10n.es.aeat.map.tax"].search(
                [
                    ("model", "=", self.number),
                    "|", ("date_from", "<=", self.date_start), ("date_from", "=", False),
                    "|", ("date_to", ">=", self.date_end), ("date_to", "=", False),
                ],
                limit=1,
            )

            if not tax_code_map:
                _logger.warning("No se encontró mapa de impuestos.")
                return

            # 2. Obtener impuestos relevantes
            report_taxes = self.env["account.tax"]
            for line in tax_code_map.map_line_ids:
                report_taxes |= line.get_taxes_for_company(self.company_id)

            if not report_taxes:
                _logger.warning("No hay impuestos configurados en el mapa.")
                return

            # 3. AGRUPAMIENTO POR DICCIONARIO (La clave del éxito)
            # Clave: (partner, real_estate, tax)
            # Valor: Recordset de líneas
            grouped_data = {}
            
            # Traemos todas las líneas de golpe (mucho más rápido)
            all_move_lines = self.tax_line_ids.mapped("move_line_ids")
            _logger.info(f"Procesando {len(all_move_lines)} líneas contables...")

            for line in all_move_lines:
                # Buscamos qué impuesto de esta línea pertenece al modelo 180
                # Intersección entre los impuestos de la línea y los del reporte
                line_taxes = (line.tax_ids | line.tax_line_id) & report_taxes
                
                emplacement = line.move_id.emplacement_id

                for tax in line_taxes:
                    # AQUÍ ESTÁ LA SOLUCIÓN:
                    # Usamos el objeto real_estate tal cual. Si está vacío, la clave tendrá un "False"
                    # y Odoo lo gestionará como un grupo válido, en lugar de ignorarlo.
                    key = (line.partner_id, emplacement, tax)
                    
                    if key not in grouped_data:
                        grouped_data[key] = self.env['account.move.line']
                    grouped_data[key] |= line

            _logger.info(f"Datos agrupados en {len(grouped_data)} perceptores distintos.")

            # 4. Crear registros
            perceptorObj = self.env["recipient.record"]
            created_count = 0

            for (partner, emplacement, tax), lines in grouped_data.items():
                
                # Calculamos base (Debe - Haber)
                base = sum(lines.mapped("debit")) - sum(lines.mapped("credit"))
                
                # Cálculo de la retención
                cuota_percent = tax.amount
                retention_amount = base * (cuota_percent / 100) * -1

                sign = " "
                if base <= 0:
                    sign = "N"

                # Creamos el registro
                # Si real_estate era un recordset vacío, .id devuelve False, que es correcto para escribir.
                perceptorObj.create({
                    "report_id": self.id,
                    "partner_id": partner.id,
                    "emplacement_id": emplacement.id if emplacement else False,
                    "l10n_es_aeat_real_estate_id": False,
                    "sign": sign,
                    "retentions_base": base,
                    "retentions_fee": retention_amount,
                    "retentions_percentage": cuota_percent,
                    "accrual_year": self.year,
                    "base_move_line_ids": [(6, 0, lines.ids)],
                })
                created_count += 1

            _logger.info(f">>> FIN. Creados {created_count} registros de perceptores. <<<")

    @api.model
    def action_init_hook(self):
        mod115_ids = self.env["l10n.es.aeat.map.tax"].search([("model", "=", 115)])
        mod180_ids = self.env["l10n.es.aeat.map.tax"].search([("model", "=", 180)])
        # Eliminar mod180
        mod180_ids.mapped("map_line_ids").unlink()
        mod180_ids.unlink()
        # Duplicar mod115
        for mod115 in mod115_ids:
            new_180 = mod115.copy({"model": 180})
            for map_line in mod115.map_line_ids:
                map_line.copy({"map_parent_id": new_180.id})
        return True
