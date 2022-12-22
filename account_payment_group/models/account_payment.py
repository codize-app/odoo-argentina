from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry', required=True, readonly=False, ondelete='cascade',
        check_company=True)

    payment_group_id = fields.Many2one(
        'account.payment.group',
        'Recibo',
        ondelete='cascade',
        readonly=True,
    )
    # we add this field so company can be send in context when adding payments
    # before payment group is saved
    payment_group_company_id = fields.Many2one(
        related='payment_group_id.company_id',
        string='Payment Group Company',
    )
    # we make a copy without transfer option, we try with related but it
    # does not works
    payment_type_copy = fields.Selection(
        selection=[('outbound', 'Enviar Dinero'), ('inbound', 'Recibir Dinero')],
        compute='_compute_payment_type_copy',
        inverse='_inverse_payment_type_copy',
        string='Tipo de Pago (sin transferencia)'
    )
    signed_amount = fields.Monetary(
        string='Monto',
        compute='_compute_signed_amount',
    )
    signed_amount_company_currency = fields.Monetary(
        string='Monto del Pago en la Moneda de la Empresa',
        compute='_compute_signed_amount',
        currency_field='company_currency_id',
    )
    amount_company_currency = fields.Monetary(
        string='Monto en la Moneda de la Empresa',
        compute='_compute_amount_company_currency',
        inverse='_inverse_amount_company_currency',
        currency_field='company_currency_id',
    )
    other_currency = fields.Boolean(
        compute='_compute_other_currency',
    )
    force_amount_company_currency = fields.Monetary(
        string='Monto Forzado en la Moneda de la Empresa',
        currency_field='company_currency_id',
        copy=False,
    )
    exchange_rate = fields.Float(
        string='Tipo de Cambio',
        #compute='_compute_exchange_rate',
        # readonly=False,
        # inverse='_inverse_exchange_rate',
        digits=(16, 4),
    )
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Moneda de compañía',
    )

    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        if not any(field_name in changed_fields for field_name in (
            'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
            'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'journal_id',
        )):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):
            if not pay.payment_group_id:
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                # Make sure to preserve the write-off amount.
                # This allows to create a new payment with custom 'line_ids'.

                if liquidity_lines and counterpart_lines and writeoff_lines:

                    counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
                    writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))

                    # To be consistent with the payment_difference made in account.payment.register,
                    # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                    # Since the write is already done at this point, we need to base the computation on accounting values.
                    if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                        sign = -1
                    else:
                        sign = 1
                    writeoff_amount = abs(writeoff_amount) * sign

                    write_off_line_vals = {
                        'name': writeoff_lines[0].name,
                        'amount': writeoff_amount,
                        'account_id': writeoff_lines[0].account_id.id,
                    }
                else:
                    write_off_line_vals = {}

                line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

                line_ids_commands = []
                if liquidity_lines:
                    line_ids_commands.append((1, liquidity_lines.id, line_vals_list[0]))
                else:
                    line_ids_commands.append((0, 0, line_vals_list[0]))
                if counterpart_lines:
                    line_ids_commands.append((1, counterpart_lines.id, line_vals_list[1]))
                else:
                    line_ids_commands.append((0, 0, line_vals_list[1]))

                for line in writeoff_lines:
                    line_ids_commands.append((2, line.id))

                for extra_line_vals in line_vals_list[2:]:
                    line_ids_commands.append((0, 0, extra_line_vals))

                # Update the existing journal items.
                # If dealing with multiple write-off lines, they are dropped and a new one is generated.

                pay.move_id.write({
                    'partner_id': pay.partner_id.id,
                    'currency_id': pay.currency_id.id,
                    'partner_bank_id': pay.partner_bank_id.id,
                    'line_ids': line_ids_commands,
                })

    @api.depends('amount', 'payment_type', 'partner_type', 'amount_company_currency')
    def _compute_signed_amount(self):
        for rec in self:
            sign = 1.0
            if (
                    (rec.partner_type == 'supplier' and
                        rec.payment_type == 'inbound') or
                    (rec.partner_type == 'customer' and
                        rec.payment_type == 'outbound')):
                sign = -1.0
            rec.signed_amount = rec.amount and rec.amount * sign
            rec.signed_amount_company_currency = (
                rec.amount_company_currency and
                rec.amount_company_currency * sign)

    # TODO check why we get error with depend on company_id and fix it
    # (recursive dependency?). The error is on paymentrs tree/form view
    # @api.depends('currency_id', 'company_id')
    @api.depends('currency_id')
    def _compute_other_currency(self):
        for rec in self:
            rec.other_currency = False
            if rec.company_currency_id and rec.currency_id and \
               rec.company_currency_id != rec.currency_id:
                rec.other_currency = True

    @api.depends('amount', 'other_currency', 'amount_company_currency')
    def _compute_exchange_rate(self):
        for rec in self.filtered('other_currency'):
            rec.exchange_rate = rec.amount and (
                rec.amount_company_currency / rec.amount) or 0.0

    # this onchange is necesary because odoo, sometimes, re-compute
    # and overwrites amount_company_currency. That happends due to an issue
    # with rounding of amount field (amount field is not change but due to
    # rouding odoo believes amount has changed)
    @api.onchange('amount_company_currency')
    def _inverse_amount_company_currency(self):
        for rec in self:
            if rec.other_currency and rec.amount_company_currency != \
                    rec.currency_id._convert(
                        rec.amount, rec.company_id.currency_id,
                        rec.company_id, rec.date):
                force_amount_company_currency = rec.amount_company_currency
            else:
                force_amount_company_currency = False
            rec.force_amount_company_currency = force_amount_company_currency

    @api.depends('amount', 'other_currency', 'force_amount_company_currency')
    def _compute_amount_company_currency(self):
        """
        * Si las monedas son iguales devuelve 1
        * si no, si hay force_amount_company_currency, devuelve ese valor
        * sino, devuelve el amount convertido a la moneda de la cia
        """
        for rec in self:
            if not rec.other_currency:
                amount_company_currency = rec.amount
            elif rec.force_amount_company_currency:
                amount_company_currency = rec.force_amount_company_currency
            else:
                amount_company_currency = rec.currency_id._convert(
                    rec.amount, rec.company_id.currency_id,
                    rec.company_id, rec.date)
            rec.amount_company_currency = amount_company_currency

    @api.onchange('payment_type_copy')
    def _inverse_payment_type_copy(self):
        for rec in self:
            # if false, then it is a transfer
            rec.payment_type = (
                rec.payment_type_copy and rec.payment_type_copy or 'transfer')

    @api.depends('payment_type')
    def _compute_payment_type_copy(self):
        for rec in self:
            if rec.payment_type == 'transfer':
                continue
            rec.payment_type_copy = rec.payment_type

    def get_journals_domain(self):
        domain = super(AccountPayment, self).get_journals_domain()
        if self.payment_group_company_id:
            domain.append(
                ('company_id', '=', self.payment_group_company_id.id))
        return domain

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        """
        we disable change of partner_type if we came from a payment_group
        but we still reset the journal
        """
        if not self._context.get('payment_group'):
            return super(AccountPayment, self)._onchange_payment_type()
        self.journal_id = False

    @api.constrains('payment_group_id', 'payment_type')
    def check_payment_group(self):
        # odoo tests don't create payments with payment gorups
        if self.env.registry.in_test_mode():
            return True
        for rec in self:
            receivable_payable = all([
                x['move_line'].account_id.internal_type in [
                    'receivable', 'payable']
                for x in self._context.get('counterpart_aml_dicts', [])])
            if rec.partner_type and rec.partner_id and receivable_payable and \
               not rec.payment_group_id:
                raise ValidationError(_(
                    'Payments with partners must be created from '
                    'payments groups'))
            # transfers or payments from bank reconciliation without partners
            elif not rec.partner_type and rec.payment_group_id:
                raise ValidationError(_(
                    "Payments without partners (usually transfers) cant't "
                    "have a related payment group"))

    @api.model
    def get_amls(self):
        """ Review parameters of process_reconciliation() method and transform
        them to amls recordset. this one is return to recompute the payment
        values
         context keys(
            'counterpart_aml_dicts', 'new_aml_dicts', 'payment_aml_rec')
         :return: account move line recorset
        """
        counterpart_aml_data = self._context.get('counterpart_aml_dicts', [])
        new_aml_data = self._context.get('new_aml_dicts', [])
        amls = self.env['account.move.line']
        if counterpart_aml_data:
            for item in counterpart_aml_data:
                amls |= item.get(
                    'move_line', self.env['account.move.line'])
        if new_aml_data:
            for aml_values in new_aml_data:
                amls |= amls.new(aml_values)
        return amls

    @api.model
    def infer_partner_info(self, vals):
        """ Odoo way to to interpret the partner_id, partner_type is not
        usefull for us because in some time they leave this ones empty and
        we need them in order to create the payment group.

        In this method will try to improve infer when it has a debt related
        taking into account the account type of the line to concile, and
        computing the partner if this ones is not setted when concile
        operation.

        return dictionary with keys (partner_id, partner_type)
        """
        res = {}
        # Get related amls
        amls = self.get_amls()
        if not amls:
            return res

        # odoo manda partner type segun si el pago es positivo o no, nosotros
        # mejoramos infiriendo a partir de que tipo de deuda se esta pagando
        partner_type = False
        internal_type = amls.mapped('account_id.internal_type')
        if len(internal_type) == 1:
            if internal_type == ['payable']:
                partner_type = 'supplier'
            elif internal_type == ['receivable']:
                partner_type = 'customer'
            if partner_type:
                res.update({'partner_type': partner_type})

        # por mas que el usuario no haya selecccionado partner, si esta pagando
        # deuda usamos el partner de esa deuda
        partner_id = vals.get('partner_id', False)
        if not partner_id and len(amls.mapped('partner_id')) == 1:
            partner_id = amls.mapped('partner_id').id
            res.update({'partner_id': partner_id})

        return res

    @api.model
    def create(self, vals):
        """ When payments are created from bank reconciliation create the
        Payment group before creating payment to avoid raising error, only
        apply when the all the counterpart account are receivable/payable """
        # Si viene counterpart_aml entonces estamos viniendo de una
        # conciliacion desde el wizard
        new_aml_dicts = self._context.get('new_aml_dicts', [])
        counterpart_aml_data = self._context.get('counterpart_aml_dicts', [])
        if counterpart_aml_data or new_aml_dicts:
            vals.update(self.infer_partner_info(vals))

        create_from_statement = self._context.get(
            'create_from_statement', False) and vals.get('partner_type') \
            and vals.get('partner_id') and all([
                x['move_line'].account_id.internal_type in [
                    'receivable', 'payable']
                for x in counterpart_aml_data])
        create_from_expense = self._context.get('create_from_expense', False)
        create_from_website = self._context.get('create_from_website', False)
        # NOTE: This is required at least from POS when we do not have
        # partner_id and we do not want a payment group in tha case.
        create_payment_group = \
            create_from_statement or create_from_website or create_from_expense
        if create_payment_group:
            company_id = self.env['account.journal'].browse(
                vals.get('journal_id')).company_id.id
            payment_group = self.env['account.payment.group'].create({
                'company_id': company_id,
                'partner_type': vals.get('partner_type'),
                'partner_id': vals.get('partner_id'),
                'payment_date': vals.get('date', fields.Date.context_today(self)),
                'communication': vals.get('communication'),
            })
            vals['payment_group_id'] = payment_group.id
        payment = super(AccountPayment, self).create(vals)
        if create_payment_group:
            payment.payment_group_id.post()
        return payment

    @api.depends('invoice_line_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        """
        If we are paying a payment gorup with paylines, we use account
        of lines that are going to be paid
        """
        for rec in self:
            to_pay_account = rec.payment_group_id.to_pay_move_line_ids.mapped(
                'account_id')
            if len(to_pay_account) > 1:
                raise ValidationError(_(
                    'To Pay Lines must be of the same account!'))
            elif len(to_pay_account) == 1:
                rec.destination_account_id = to_pay_account[0]
            else:
                super(AccountPayment, rec)._compute_destination_account_id()

    def show_details(self):
        """
        Metodo para mostrar form editable de payment, principalmente para ser
        usado cuando hacemos ajustes y el payment group esta confirmado pero
        queremos editar una linea
        """
        return {
            'name': _('Payment Lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'target': 'new',
            'res_id': self.id,
            'context': self._context,
        }

    def _get_shared_move_line_vals(
            self, debit, credit, amount_currency, move_id, invoice_id=False):
        """
        Si se esta forzando importe en moneda de cia, usamos este importe
        para debito/credito
        """
        res = super(AccountPayment, self)._get_shared_move_line_vals(
            debit, credit, amount_currency, move_id, invoice_id=invoice_id)
        if self.force_amount_company_currency:
            if res.get('debit', False):
                res['debit'] = self.force_amount_company_currency
            if res.get('credit', False):
                res['credit'] = self.force_amount_company_currency
        return res

    def _get_move_vals(self, journal=None):
        """If we have a communication on payment group append it before
        payment communication
        """
        vals = super(AccountPayment, self)._get_move_vals(journal=journal)
        if self.payment_group_id.communication:
            vals['ref'] = "%s%s" % (
                self.payment_group_id.communication,
                self.communication and ": %s" % self.communication or "")
        return vals

    def _prepare_payment_moves(self):
        res = super(AccountPayment, self)._prepare_payment_moves()
        #for i,rec in enumerate(self):
        #    if rec.signed_amount_company_currency != line.credit:
        for i,rec in enumerate(self):
            if rec.currency_id.id != rec.company_id.currency_id.id and rec.payment_type == 'inbound':
                amount_debit = res[i]['line_ids'][0][2]['debit']
                amount_credit = res[i]['line_ids'][0][2]['credit']
                if amount_credit > 0 and rec.signed_amount_company_currency != amount_credit:
                    #raise ValidationError('estamos aca %s %s'%(amount_credit,res[0]['line_ids'][0][2]))
                    res[i]['line_ids'][0][2]['credit'] = rec.signed_amount_company_currency
                amount_debit = res[i]['line_ids'][1][2]['debit']
                amount_credit = res[i]['line_ids'][1][2]['credit']
                if amount_debit > 0 and rec.signed_amount_company_currency != amount_debit:
                    #raise ValidationError('estamos aca %s %s'%(amount_credit,res[0]['line_ids'][0][2]))
                    res[i]['line_ids'][1][2]['debit'] = rec.signed_amount_company_currency
        return res
