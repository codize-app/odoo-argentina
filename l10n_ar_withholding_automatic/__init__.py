##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from . import models
from . import wizards


def post_init_hook(env):
    inbound_method = env.ref(
        'l10n_ar_withholding_automatic.account_payment_method_in_withholding',
        raise_if_not_found=False)
    outbound_method = env.ref(
        'l10n_ar_withholding_automatic.account_payment_method_out_withholding',
        raise_if_not_found=False)
    if not inbound_method or not outbound_method:
        return
    journals = env['account.journal'].search([('type', 'in', ['bank', 'cash'])])
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
