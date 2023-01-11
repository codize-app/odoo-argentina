# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _compute_print_withholding(self):
            for rec in self:
                if rec.state == 'posted':
                    if rec.tax_withholding_id:
                        rec.print_withholding = True
                    else:
                        rec.print_withholding = False
                else:
                    rec.print_withholding = False

    tax_withholding_id = fields.Many2one(
        'account.tax',
        string='Impuesto de retención',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    withholding_number = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="If you don't set a number we will add a number automatically "
        "from a sequence that should be configured on the Withholding Tax"
    )
    withholding_base_amount = fields.Monetary(
        string='Monto base de retención',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    communication = fields.Text('Notas')
    automatic = fields.Boolean(
    )
    withholding_accumulated_payments = fields.Selection(
        related='tax_withholding_id.withholding_accumulated_payments',
        readonly=True,
    )
    withholdable_invoiced_amount = fields.Float(
        'Importe imputado sujeto a retención',
        readonly=True,
    )
    withholdable_advanced_amount = fields.Float(
        'Importe a cuenta sujeto a retención',
        readonly=True,
    )
    accumulated_amount = fields.Float(
        readonly=True,
    )
    total_amount = fields.Float(
        readonly=True,
    )
    withholding_non_taxable_minimum = fields.Float(
        'Mínimo no imponible',
        readonly=True,
    )
    withholding_non_taxable_amount = fields.Float(
        'Monto no imponible',
        readonly=True,
    )
    withholdable_base_amount = fields.Float(
        readonly=True,
    )
    period_withholding_amount = fields.Float('Retención del período')
    previous_withholding_amount = fields.Float(
        readonly=True,
    )
    computed_withholding_amount = fields.Float('Retención calculada')
    used_withholding = fields.Boolean(string='Usado en retenciones')
    print_withholding = fields.Boolean('Imprimir Retenciones', compute=_compute_print_withholding)

    def btn_print_withholding(self):
            self.ensure_one()
            return self.env.ref('l10n_ar_withholding.account_payment_withholdings').report_action(self)

    def _get_counterpart_move_line_vals(self, invoice=False):
        vals = super(AccountPayment, self)._get_counterpart_move_line_vals(
            invoice=invoice)
        if self.payment_group_id:
            taxes = self.payment_group_id.payment_ids.filtered(
                lambda x: x.payment_method_code == 'withholding').mapped(
                'tax_withholding_id')
            vals['tax_ids'] = [(6, False, taxes.ids)]
        return vals

    def action_post(self):
        without_number = self.filtered(
            lambda x: x.tax_withholding_id and not x.withholding_number)
        without_sequence = without_number.filtered(
            lambda x: not x.tax_withholding_id.withholding_sequence_id)
        if without_sequence:
            raise UserError(_(
                'No puede validar pagos con retenciones que no tengan número '
                'de retención. Recomendamos agregar una secuencia a los '
                'impuestos de retención correspondientes. Id de pagos: %s') % (
                without_sequence.ids))

        for payment in (without_number - without_sequence):
            payment.withholding_number = \
                payment.tax_withholding_id.withholding_sequence_id.next_by_id()
            #Si el pago de retencion no tiene nombre o es '/' lo seteamos con el mismo nombre que su numero para no tener problemas
            # con account_payment_fix
            if payment.name == '/':
                payment.write({'name': payment.withholding_number})

        return super(AccountPayment, self).action_post()

    def _get_liquidity_move_line_vals(self, amount):
        vals = super(AccountPayment, self)._get_liquidity_move_line_vals(
            amount)
        if self.payment_method_code == 'withholding':
            if self.payment_type == 'transfer':
                raise UserError(_(
                    'You can not use withholdings on transfers!'))
            if (
                    (self.partner_type == 'customer' and
                        self.payment_type == 'inbound') or
                    (self.partner_type == 'supplier' and
                        self.payment_type == 'outbound')):
                account = self.tax_withholding_id.account_id
            else:
                account = self.tax_withholding_id.refund_account_id
            if account:
                vals['account_id'] = account.id
            vals['name'] = self.withholding_number or '/'
            vals['tax_line_id'] = self.tax_withholding_id.id
        return vals

    def _compute_payment_method_description(self):
        payments = self.filtered(
            lambda x: x.payment_method_code == 'withholding')
        for rec in payments:
            name = rec.tax_withholding_id.name or rec.payment_method_id.name
            rec.payment_method_description = name
        return super(
            AccountPayment,
            (self - payments))._compute_payment_method_description()
    
    def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        '''
        self.ensure_one()

        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']

        for line in self.move_id.line_ids:
            if line.account_id in self._get_valid_liquidity_accounts():
                liquidity_lines += line
            elif line.account_id.internal_type in ('receivable', 'payable') or line.partner_id == line.company_id.partner_id:
                counterpart_lines += line
            #Modificación hecha para múltiples pagos de retención en un mismo grupo de pagos
            elif self.tax_withholding_id:
                liquidity_lines += line
            else:
                writeoff_lines += line

        return liquidity_lines, counterpart_lines, writeoff_lines


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['withholding'] = {'mode': 'multi', 'domain': [('type', '=', 'bank', 'cash')]}
        return res
