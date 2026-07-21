from odoo import models, api

class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['withholding'] = {'mode': 'multi', 'domain': [('type', 'in', ['cash', 'bank'])]}
        return res

    @api.model
    def _setup_withholding_on_journals(self):
        inbound_method = self.env.ref(
            'l10n_ar_withholding_automatic.account_payment_method_in_withholding',
            raise_if_not_found=False)
        outbound_method = self.env.ref(
            'l10n_ar_withholding_automatic.account_payment_method_out_withholding',
            raise_if_not_found=False)
        if not inbound_method or not outbound_method:
            return
        journals = self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])])
        for journal in journals:
            if not journal.inbound_payment_method_line_ids.filtered(
                    lambda l: l.payment_method_id == inbound_method):
                journal.write({
                    'inbound_payment_method_line_ids': [
                        (0, 0, {'payment_method_id': inbound_method.id})]
                })
            if not journal.outbound_payment_method_line_ids.filtered(
                    lambda l: l.payment_method_id == outbound_method):
                journal.write({
                    'outbound_payment_method_line_ids': [
                        (0, 0, {'payment_method_id': outbound_method.id})]
                })
