import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Create a payment group for every existing payment
    """
    payments = env['account.payment'].search(
        [('partner_id', '!=', False)])

    for payment in payments:
        _logger.info('creating payment group for payment %s' % payment.id)
        env['account.payment.group'].create({
            'company_id': payment.company_id.id,
            'partner_type': payment.partner_type,
            'partner_id': payment.partner_id.id,
            'payment_date': payment.date,
            'communication': payment.memo,
            'payment_ids': [(4, payment.id, False)],
            'state': (
                payment.state in ['sent', 'reconciled'] and
                'posted' or payment.state),
        })
