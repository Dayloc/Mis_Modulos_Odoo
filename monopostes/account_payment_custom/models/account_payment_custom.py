# -*- coding: utf-8 -*-

from odoo import _,api, fields, models

class AccountPaymentCustom(models.Model):
    _inherit = 'account.batch.payment'

    def _send_after_validation(self):
        self.ensure_one()
        if self.payment_ids:
            # Usamos context para evitar el envío de notificaciones
            # 'tracking_disable' evita que se disparen los correos de seguimiento/plantillas
            self.payment_ids.with_context(tracking_disable=True, mail_notify_force_send=False).mark_as_sent()

            if self.file_generation_enabled:
                return self.export_batch_payment()