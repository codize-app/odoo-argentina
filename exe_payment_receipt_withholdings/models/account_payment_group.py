from odoo import models, _
from odoo.exceptions import UserError


class AccountPaymentGroup(models.Model):
    _inherit = 'account.payment.group'

    def _exe_receipt_withholding_payments(self):
        self.ensure_one()
        if self.partner_type != 'supplier' or self.state != 'posted':
            return self.env['account.payment']
        payments = self.payment_ids.filtered(lambda payment: (
            payment.tax_withholding_id
            and payment.state in ('in_process', 'paid')
            and payment.move_id.state == 'posted'
            and not payment.currency_id.is_zero(payment.amount)
        )).sorted('id')
        for payment in payments:
            if payment.company_id != self.company_id:
                raise UserError(_('El pago de retención pertenece a otra empresa.'))
            if not payment.withholding_number:
                raise UserError(_(
                    'La retención del pago %(payment)s no tiene número de certificado. '
                    'Revise el pago antes de imprimir.', payment=payment.display_name,
                ))
        return payments
