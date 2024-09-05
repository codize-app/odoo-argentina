from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_group_ids = fields.Many2many(
        'account.payment.group',
        'account_move_line_payment_group_to_pay_rel',
        'to_pay_line_id',
        'payment_group_id',
        string="Grupos de Pago",
        readonly=True,
        auto_join=True,
    )
    payment_group_matched_amount = fields.Monetary(
        compute='_compute_payment_group_matched_amount',
        currency_field='company_currency_id',
    )
    financial_amount_residual = fields.Monetary(
        compute='_compute_financial_amounts',
        string='Residual Financial Amount',
        currency_field='company_currency_id',
    )
    financial_amount = fields.Monetary(
        compute='_compute_financial_amounts',
        string='Financial Amount',
        currency_field='company_currency_id',
    )

    @api.depends('debit', 'credit')
    def _compute_financial_amounts(self):
        date = fields.Date.today()
        for line in self:
            financial_amount = (
                line.currency_id and line.currency_id._convert(
                    line.amount_currency,
                    line.company_id.currency_id,
                    line.company_id, date) or (
                    line.balance))
            financial_amount_residual = (
                line.currency_id and line.currency_id._convert(
                    line.amount_residual_currency,
                    line.company_id.currency_id,
                    line.company_id, date) or
                line.amount_residual)
            line.financial_amount = financial_amount
            line.financial_amount_residual = financial_amount_residual

    def _compute_payment_group_matched_amount(self):
        """
        Recibir un payment_group_id por contexto, decimos en ese payment
        group, cuanto se pago para la lína en cuestión.
        """
        payment_group_id = self._context.get('payment_group_id')
        if not payment_group_id:
            return False
        payments = self.env['account.payment.group'].browse(
            payment_group_id).payment_ids
        # payment_move_lines = payments.mapped('move_line_ids')
        payment_move_lines = payments.mapped('invoice_line_ids')

        for rec in self:
            matched_amount = 0.0
            reconciles = self.env['account.partial.reconcile'].search([
                ('credit_move_id', 'in', payment_move_lines.ids),
                ('debit_move_id', '=', rec.id)])
            matched_amount += sum(reconciles.mapped('amount'))

            reconciles = self.env['account.partial.reconcile'].search([
                ('debit_move_id', 'in', payment_move_lines.ids),
                ('credit_move_id', '=', rec.id)])
            matched_amount -= sum(reconciles.mapped('amount'))
            rec.payment_group_matched_amount = matched_amount
