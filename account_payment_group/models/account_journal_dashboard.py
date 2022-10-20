from odoo import models, api, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def open_payments_action(self, payment_type, mode='tree'):
        if payment_type == 'transfer':
            ctx = self._context.copy()
            if mode == 'form':
                ctx.update({
                    'default_payment_type': 'transfer',
                    'default_journal_id': self.id,
                    'default_partner_type': 'customer',
                    'default_is_internal_transfer': True,
                    'is_internal_transfer': True,
                    'default_partner_id': self.company_id.partner_id.id,
                })
                action_rec = self.env.ref(
                    'account_payment_group.action_account_payments_transfer_form')
                action = action_rec.read([])[0]
                action['name'] = _('New Transfer')
                action['context'] = ctx
            else:
                action_rec = self.env.ref(
                    'account_payment_group.action_account_payments_transfer')

                action = action_rec.read([])[0]
                action['context'] = ctx
                action['domain'] = [('journal_id', '=', self.id),
                                    ('payment_type', '=', payment_type)]
            return action
        return super(AccountJournal, self).open_payments_action(payment_type)
