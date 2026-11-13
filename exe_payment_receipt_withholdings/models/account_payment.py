from odoo import api, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('state', 'tax_withholding_id', 'move_id.state')
    def _compute_print_withholding(self):
        super()._compute_print_withholding()
        for payment in self:
            payment.print_withholding = bool(
                payment.tax_withholding_id
                and payment.state in ('in_process', 'paid')
                and payment.move_id.state == 'posted'
            )
