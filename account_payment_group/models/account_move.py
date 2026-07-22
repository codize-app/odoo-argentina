from odoo import models, api, fields, _, Command
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    open_move_line_ids = fields.One2many(
        'account.move.line',
        compute='_compute_open_move_lines'
    )
    pay_now_journal_id = fields.Many2one(
        'account.journal',
        'Diario de Pagar Ahora',
        help='If you set a journal here, after invoice validation, the invoice'
        ' will be automatically paid with this journal. As manual payment'
        'method is used, only journals with manual method are shown.'
    )
    payment_group_ids = fields.Many2many(
        'account.payment.group',
        compute='_compute_payment_groups',
        string='Grupos de Pago',
    )

    def _compute_payment_groups(self):
        """
        El campo en invoices "payment_id" no lo seteamos con los payment groups
        Por eso tenemos que calcular este campo
        """
        for rec in self:
            rec.payment_group_ids = rec.line_ids.filtered(
                lambda l: l.payment_id
            ).mapped('payment_id.payment_group_id')

    def _get_tax_factor(self):
        self.ensure_one()
        return (self.amount_total and (
            self.amount_untaxed / self.amount_total) or 1.0)

    @api.depends('line_ids.account_id.account_type', 'line_ids.reconciled')
    def _compute_open_move_lines(self):
        for rec in self:
            rec.open_move_line_ids = rec.line_ids.filtered(
                lambda r: not r.reconciled and r.account_id.account_type in (
                    'liability_payable', 'asset_receivable'))

    def _post(self, soft=False):
        res = super()._post(soft=soft)
        self.pay_now()
        return res

    def pay_now(self):
        for rec in self.filtered(lambda x: x.pay_now_journal_id and x.state == 'posted' and
                                 x.payment_state in ('not_paid', 'partial')):
            pay_journal = rec.pay_now_journal_id
            if rec.move_type in ['in_invoice', 'in_refund']:
                partner_type = 'supplier'
                payment_type = 'outbound'
            else:
                partner_type = 'customer'
                payment_type = 'inbound'

            # Get the appropriate payment method line
            if payment_type == 'inbound':
                method_line = pay_journal.inbound_payment_method_line_ids[:1]
            else:
                method_line = pay_journal.outbound_payment_method_line_ids[:1]

            payment = rec.env[
                'account.payment'].with_context(pay_now=True).create({
                        'date': rec.invoice_date,
                        'partner_id': rec.commercial_partner_id.id,
                        'partner_type': partner_type,
                        'payment_type': payment_type,
                        'company_id': rec.company_id.id,
                        'journal_id': pay_journal.id,
                        'payment_method_line_id': method_line.id,
                        'to_pay_move_line_ids': [Command.set(rec.open_move_line_ids.ids)],
                    })

            # el difference es positivo para facturas (de cliente o proveedor) pero negativo para NC.
            if (partner_type == 'supplier' and payment.payment_difference >= 0.0 or
               partner_type == 'customer' and payment.payment_difference < 0.0):
                payment.payment_type = 'outbound'
                outbound_line = pay_journal.outbound_payment_method_line_ids[:1]
                payment.payment_method_line_id = outbound_line.id
            payment.amount = abs(payment.payment_difference)
            payment.action_post()

    def action_view_payment_groups(self):
        if self.move_type in ('in_invoice', 'in_refund'):
            action = self.env.ref(
                'account_payment_group.action_account_payments_group_payable')
        else:
            action = self.env.ref(
                'account_payment_group.action_account_payments_group')

        result = action.read()[0]

        if len(self.payment_group_ids) != 1:
            result['domain'] = [('id', 'in', self.payment_group_ids.ids)]
        elif len(self.payment_group_ids) == 1:
            res = self.env.ref(
                'account_payment_group.view_account_payment_group_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.payment_group_ids.id
        return result

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.pay_now_journal_id = False

    def button_cancel(self):
        self.filtered(
            lambda x: x.state == 'draft' and x.pay_now_journal_id).write(
                {'pay_now_journal_id': False})
        return super(AccountMove, self).button_cancel()

    def action_account_invoice_payment_group(self):
        self.ensure_one()
        if self.state != 'posted' or self.payment_state not in ['not_paid', 'in_payment', 'partial']:
            raise ValidationError(_('You can only register payment if invoice is posted and unpaid'))
        return {
            'name': _('Register Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment.group',
            'view_id': False,
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {
                'default_partner_id': self.partner_id.id,
                'to_pay_move_line_ids': self.open_move_line_ids.ids,
                'pop_up': True,
                'from_invoice': 'yes',
                'amount_invoice': self.amount_total,
                'invoice_id': self.id,
                'create': True,
                'default_company_id': self.company_id.id,
            },
        }

