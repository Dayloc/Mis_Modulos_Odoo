# from odoo import models, fields, api
# from datetime import date
# from odoo.tools import float_is_zero
#
#
# class AccountReportBudgetItem(models.Model):
#     _inherit = 'account.report.budget.item'
#
#     # 1. Hacemos que last_year_balance sea editable y almacenable
#     last_year_balance = fields.Float(
#         string="Saldo Año Anterior",
#         compute="_compute_budget_logic",
#         store=True,
#         readonly=False,  # Permite que el valor manual persista
#         copy=True,
#         digits=(16, 2)
#     )
#
#     last_year_balance_ui = fields.Float(
#         string="Saldo Año Ant.",
#         compute="_compute_balance_ui",
#         inverse="_inverse_balance_ui",  # Permite editar la base directamente
#         store=True,
#         copy=True,
#         digits=(16, 2)
#     )
#
#     amount = fields.Float(
#         string="Importe Real",
#         compute="_compute_budget_logic",
#         store=True,
#         readonly=False,
#         copy=True
#     )
#
#     amouunt_ui = fields.Float(
#         string='Importe',
#         compute="_compute_importe_ui",
#         inverse="_inverse_importe_ui",
#         store=False,
#         readonly=False,
#         digits=(16, 2)
#     )
#
#     percentage_adj = fields.Float(string="% Incremento", default=0.0)
#
#     # --- LÓGICA DE DUPLICACIÓN ---
#     @api.model
#     def copy(self, default=None):
#         default = default or {}
#         # Al duplicar, queremos que el 'importe' del viejo sea el 'saldo anterior' del nuevo
#         default['last_year_balance'] = self.amouunt_ui
#         # Reseteamos el incremento para que el usuario empiece de cero sobre la nueva base
#         default['percentage_adj'] = 0.0
#         return super(AccountReportBudgetItem, self).copy(default)
#
#     # --- INVERSOS PARA LA UI ---
#     def _inverse_importe_ui(self):
#         for record in self:
#             record.amount = record.amouunt_ui * -1
#
#     def _inverse_balance_ui(self):
#         for record in self:
#             record.last_year_balance = record.last_year_balance_ui * -1
#
#     @api.depends('amount')
#     def _compute_importe_ui(self):
#         for record in self:
#             record.amouunt_ui = round(record.amount * -1, 2) if record.amount else 0.0
#
#     @api.depends('last_year_balance')
#     def _compute_balance_ui(self):
#         for record in self:
#             record.last_year_balance_ui = round(record.last_year_balance * -1, 2) if record.last_year_balance else 0.0
#
#     # --- LÓGICA PRINCIPAL ---
#     @api.depends('account_id', 'date', 'percentage_adj')
#     def _compute_budget_logic(self):
#         for record in self:
#             # Solo buscamos en contabilidad si el saldo anterior es 0 o estamos en un registro nuevo
#             # Esto evita que Odoo sobrescriba tus 1.275 con los 900 contables al guardar.
#             if record.account_id and record.date and float_is_zero(record.last_year_balance, precision_digits=2):
#                 last_year = record.date.year - 1
#                 date_from = date(last_year, 1, 1)
#                 date_to = date(last_year, 12, 31)
#
#                 domain = [
#                     ('account_id', '=', record.account_id.id),
#                     ('date', '>=', date_from),
#                     ('date', '<=', date_to),
#                     ('move_id.state', '=', 'posted')
#                 ]
#
#                 aml_data = self.env['account.move.line'].read_group(domain, ['balance'], ['account_id'])
#                 record.last_year_balance = aml_data[0]['balance'] if aml_data else 0.0
#
#             # Cálculo del importe basado en la base (ya sea contable o manual)
#             incremento = record.last_year_balance * record.percentage_adj
#             record.amount = record.last_year_balance + incremento
#
#     @api.onchange('amouunt_ui')
#     def _onchange_amouunt_ui(self):
#         real_amount = self.amouunt_ui * -1
#         self.amount = real_amount
#         if self.last_year_balance and not float_is_zero(self.last_year_balance, precision_digits=2):
#             self.percentage_adj = (real_amount / self.last_year_balance) - 1
from odoo import models, fields, api
from datetime import date

from odoo.tools import float_is_zero
import logging
_logger = logging.getLogger(__name__)

class AccountReportBudget(models.Model):
    _inherit = 'account.report.budget'

    def action_duplicate_with_projection(self):
        _logger.info("=== INICIO DE PROYECCIÓN (CON RECÁLCULO DE SALDOS) ===")

        for budget in self:
            # 1. Crear la nueva cabecera
            new_budget = self.env['account.report.budget'].create({
                'name': budget.name + " (Duplicado)",
                'company_id': budget.company_id.id,
            })

            for line in budget.item_ids:

                self.env['account.report.budget.item'].create({
                    'budget_id': new_budget.id,
                    'account_id': line.account_id.id,
                    'date': line.date,

                    'percentage_adj': 0.0,  # Empezamos sin incremento

                    # Al poner 0, el sistema busca en contabilidad (ej. encuentra 1000)
                    'last_year_balance': 0.0,

                    # Al poner 0, el sistema calcula: 1000 + (0%) = 1000.
                    # El resultado final será que Importe = Saldo Año Anterior.
                    'amount': 0.0,
                })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.report.budget',
            'view_mode': 'form',
            'res_id': new_budget.id,
            'target': 'current',
        }


class AccountReportBudgetItem(models.Model):
    _inherit = 'account.report.budget.item'

    last_year_balance = fields.Float(
        string="Saldo Año Anterior",
        compute="_compute_budget_logic",
        store=True,
        copy=True,
        readonly=False,  # Importante para que acepte el valor de copy
        digits=(16, 2)
    )

    # Nuevo campo solo para la VISTA (Front-end)
    last_year_balance_ui = fields.Float(
        string="Saldo Año Ant.",
        compute="_compute_balance_ui",
        inverse="_inverse_balance_ui",
        store=True,
        copy=True,
        digits = (16, 2)
    )

    amount = fields.Float(
        string="Importe",
        compute="_compute_budget_logic",
        store=True,
        readonly=False  # Permite edición manual si lo prefieres
    )

    amouunt_ui = fields.Float(
        string='Importe',
        compute="_compute_importe_ui",
        inverse="_inverse_importe_ui",  # Permite que lo que escribas se guarde
        store=True,
        readonly=False,
        digits=(16, 2)
    )

    @api.model
    def create(self, vals):
        record = super(AccountReportBudgetItem, self).create(vals)
        if float_is_zero(record.last_year_balance, precision_digits=2) and \
                record.account_id and record.date and \
                not self.env.context.get('bypass_accounting'):
            record._compute_budget_logic()
            record._compute_importe_ui()
            record._compute_balance_ui()

        return record

    def _inverse_balance_ui(self):
        for record in self:
            record.last_year_balance = record.last_year_balance_ui * -1

    def _inverse_importe_ui(self):
        for record in self:
            # Si escribes 1230 en la UI, guardamos -1230 en amount
            record.amount = record.amouunt_ui * -1

    @api.onchange('amouunt_ui')
    def _onchange_amouunt_ui(self):
        # Primero actualizamos el valor real para el cálculo
        real_amount = self.amouunt_ui * -1
        self.amount = real_amount

        # Calculamos el porcentaje igual que antes
        if self.last_year_balance and self.last_year_balance != 0:
            # Importante: Usamos el signo real para el cálculo matemático
            self.percentage_adj = (real_amount / self.last_year_balance) - 1

    @api.depends('amount')
    def _compute_importe_ui(self):
        for record in self:
            if float_is_zero(record.amount, precision_digits=2):
                record.amouunt_ui = 0.0
            else:
                inverted = round(record.amount * -1, 2)
                # Limpieza de signo para el cero
                record.amouunt_ui = 0.0 if inverted == -0.0 else inverted

    @api.depends('last_year_balance')
    def _compute_balance_ui(self):
        for record in self:
            # Invertimos el signo: si es -5 muestra 5, si es 5 muestra -5
            record.last_year_balance_ui = record.last_year_balance * -1

    # Redefinimos amount para que dependa de nuestra lógica

    percentage_adj = fields.Float(string="% Incremento", default=0.0)

    @api.depends('account_id', 'date', 'percentage_adj')
    def _compute_budget_logic(self):
        for record in self:
            if self.env.context.get('bypass_accounting') or \
                    not float_is_zero(record.last_year_balance, precision_digits=2):
                incremento = record.last_year_balance * record.percentage_adj
                record.amount = record.last_year_balance + incremento
                continue
            fetched_balance = 0.0

            if record.account_id and record.date:
                last_year = record.date.year - 1
                date_from = date(last_year, 1, 1)
                date_to = date(last_year, 12, 31)

                domain = [
                    ('account_id', '=', record.account_id.id),
                    ('date', '>=', date_from),
                    ('date', '<=', date_to),
                    ('move_id.state', '=', 'posted')
                ]

                aml_data = self.env['account.move.line'].read_group(
                    domain, ['balance'], ['account_id']
                )

                if aml_data:
                    fetched_balance = aml_data[0]['balance']
            record.last_year_balance = fetched_balance
            incremento = fetched_balance * record.percentage_adj
            record.amount = fetched_balance + incremento


    @api.onchange('amount')
    def _onchange_amount(self):
        if self.last_year_balance and self.last_year_balance != 0:
            self.percentage_adj = (self.amount / self.last_year_balance) - 1