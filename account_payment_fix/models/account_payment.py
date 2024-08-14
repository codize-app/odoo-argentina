from odoo import fields, models, api
# from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    #state = fields.Selection(track_visibility='always')
    #amount = fields.Monetary(track_visibility='always')
    #partner_id = fields.Many2one(track_visibility='always')
    #journal_id = fields.Many2one(track_visibility='always')
    #destination_journal_id = fields.Many2one(track_visibility='always')
    #currency_id = fields.Many2one(track_visibility='always')
    # campo a ser extendido y mostrar un nombre detemrinado en las lineas de
    # pago de un payment group o donde se desee (por ej. con cheque, retención,
    # etc)
    payment_method_description = fields.Char(
        compute='_compute_payment_method_description',
        string='Método de Pago',
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
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Moneda de la Compañía',
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

    @api.depends('amount', 'other_currency', 'amount_company_currency')
    def _compute_exchange_rate(self):
        for rec in self.filtered('other_currency'):
            rec.exchange_rate = rec.amount and (
                rec.amount_company_currency / rec.amount) or 0.0

    @api.onchange('amount_company_currency')
    def _inverse_amount_company_currency(self):
        for rec in self:
            if rec.other_currency and rec.amount_company_currency != \
                    rec.currency_id._convert(
                        rec.amount, rec.company_id.currency_id,
                        rec.company_id, rec.payment_date):
                force_amount_company_currency = rec.amount_company_currency
            else:
                force_amount_company_currency = False
            rec.force_amount_company_currency = force_amount_company_currency

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

    @api.depends('currency_id')
    def _compute_other_currency(self):
        for rec in self:
            rec.other_currency = False
            if rec.company_currency_id and rec.currency_id and \
               rec.company_currency_id != rec.currency_id:
                rec.other_currency = True

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
                    rec.company_id, rec.payment_date)
            rec.amount_company_currency = amount_company_currency

    def _compute_payment_method_description(self):
        for rec in self:
            rec.payment_method_description = rec.payment_method_id.display_name

    # nuevo campo funcion para definir dominio de los metodos
    payment_method_ids = fields.Many2many(
        'account.payment.method',
        compute='_compute_payment_methods',
        string='Available payment methods',
    )
    journal_ids = fields.Many2many(
        'account.journal',
        compute='_compute_journals'
    )
    # journal_at_least_type = fields.Char(
    #     compute='_compute_journal_at_least_type'
    # )
    destination_journal_ids = fields.Many2many(
        'account.journal',
        compute='_compute_destination_journals'
    )

    @api.depends(
        # 'payment_type',
        'journal_id',
    )
    def _compute_destination_journals(self):
        for rec in self:
            domain = [
                ('type', 'in', ('bank', 'cash')),
                # al final pensamos mejor no agregar esta restricción, por ej,
                # para poder transferir a tarjeta a pagar. Esto solo se usa
                # en transferencias
                # ('at_least_one_inbound', '=', True),
                ('company_id', '=', rec.journal_id.company_id.id),
                ('id', '!=', rec.journal_id.id),
            ]
            rec.destination_journal_ids = rec.journal_ids.search(domain)

    # @api.depends(
    #     'payment_type',
    # )
    # def _compute_journal_at_least_type(self):
    #     for rec in self:
    #         if rec.payment_type == 'inbound':
    #             journal_at_least_type = 'at_least_one_inbound'
    #         else:
    #             journal_at_least_type = 'at_least_one_outbound'
    #         rec.journal_at_least_type = journal_at_least_type

    def get_journals_domain(self):
        """
        We get domain here so it can be inherited
        """
        self.ensure_one()
        domain = [('type', 'in', ('bank', 'cash'))]
        #if self.payment_type == 'inbound':
        #    domain.append(('at_least_one_inbound', '=', True))
        # Al final dejamos que para transferencias se pueda elegir
        # cualquier sin importar si tiene outbound o no
        # else:
        #elif self.payment_type == 'outbound':
        #    domain.append(('at_least_one_outbound', '=', True))
        return domain

    @api.depends(
        'payment_type',
    )
    def _compute_journals(self):
        for rec in self:
            rec.journal_ids = rec.journal_ids.search(rec.get_journals_domain())

    @api.depends(
        'journal_id.outbound_payment_method_ids',
        'journal_id.inbound_payment_method_ids',
        'payment_type',
    )
    def _compute_payment_methods(self):
        for rec in self:
            if rec.payment_type in ('outbound', 'transfer'):
                methods = rec.journal_id.outbound_payment_method_ids
            else:
                methods = rec.journal_id.inbound_payment_method_ids
            rec.payment_method_ids = methods

    @api.onchange('currency_id')
    def _onchange_currency(self):
        """ Anulamos metodo nativo que pisa el monto remanente que pasamos
        por contexto TODO ver si podemos re-incorporar esto y hasta extender
        _compute_payment_amount para que el monto se calcule bien aun usando
        el save and new"""
        return False

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        """
        Sobre escribimos y desactivamos la parte del dominio de la funcion
        original ya que se pierde si se vuelve a entrar
        """
        if not self.invoice_line_ids:
            # Set default partner type for the payment type
            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
            elif self.payment_type == 'outbound':
                self.partner_type = 'supplier'
            else:
                self.partner_type = False
            # limpiamos journal ya que podria no estar disponible para la nueva
            # operacion y ademas para que se limpien los payment methods
            self.journal_id = False
        # # Set payment method domain
        # res = self._onchange_journal()
        # if not res.get('domain', {}):
        #     res['domain'] = {}
        # res['domain']['journal_id'] = self.payment_type == 'inbound' and [
        #     ('at_least_one_inbound', '=', True)] or [
        #     ('at_least_one_outbound', '=', True)]
        # res['domain']['journal_id'].append(('type', 'in', ('bank', 'cash')))
        # return res

    # @api.onchange('partner_type')
    def _onchange_partner_type(self):
        """
        Agregasmos dominio en vista ya que se pierde si se vuelve a entrar
        Anulamos funcion original porque no haria falta
        """
        return False

    def _onchange_amount(self):
        """
        Anulamos este onchange que termina cambiando el domain de journals
        y no es compatible con multicia y se pierde al guardar.
        TODO: ver que odoo con este onchange llama a
        _compute_journal_domain_and_types quien devolveria un journal generico
        cuando el importe sea cero, imagino que para hacer ajustes por
        diferencias de cambio
        """
        return True

    @api.onchange('journal_id')
    def _onchange_journal(self):
        """
        Sobre escribimos y desactivamos la parte del dominio de la funcion
        original ya que se pierde si se vuelve a entrar
        TODO: ver que odoo con este onchange llama a
        _compute_journal_domain_and_types quien devolveria un journal generico
        cuando el importe sea cero, imagino que para hacer ajustes por
        diferencias de cambio
        """
        if self.journal_id:

            #La numeración se recrea en la validación ya que puede ser erronea si hay mas de una fila por journla
            if not self.reconciled_bill_ids:
                self.move_id.journal_id = self.journal_id.id
                self.name.replace('False', self.journal_id.code)
                self.move_id._set_next_sequence()
                self.name =self.move_id.name


            self.currency_id = (
                self.journal_id.currency_id or self.company_id.currency_id)
            # Set default payment method
            # (we consider the first to be the default one)
            payment_methods = (
                self.payment_type == 'inbound' and
                self.journal_id.inbound_payment_method_ids or
                self.journal_id.outbound_payment_method_ids)
            # si es una transferencia y no hay payment method de origen,
            # forzamos manual
            if not payment_methods and self.payment_type == 'transfer':
                payment_methods = self.env.ref(
                    'account.account_payment_method_manual_out')
            self.payment_method_id = (
                payment_methods and payment_methods[0] or False)
            # si se eligió de origen el mismo diario de destino, lo resetiamos
            #if self.journal_id == self.destination_journal_id:
            #    self.destination_journal_id = False
        #     # Set payment method domain
        #     # (restrict to methods enabled for the journal and to selected
        #     # payment type)
        #     payment_type = self.payment_type in (
        #         'outbound', 'transfer') and 'outbound' or 'inbound'
        #     return {
        #         'domain': {
        #             'payment_method_id': [
        #                 ('payment_type', '=', payment_type),
        #                 ('id', 'in', payment_methods.ids)]}}
        # return {}

    @api.depends('invoice_line_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        """
        We send with_company on context so payments can be created from parent
        companies. We try to send force_company on self but it doesnt works, it
        only works sending it on partner
        """
        res = super(AccountPayment, self)._compute_destination_account_id()
        for rec in self.filtered(
                lambda x: not x.invoice_line_ids and x.payment_type != 'transfer'):
            partner = self.partner_id.with_context(
                with_company=self.company_id.id)
            partner = self.partner_id
            if self.partner_type == 'customer':
                self.destination_account_id = (
                    partner.property_account_receivable_id.id)
            else:
                self.destination_account_id = (
                    partner.property_account_payable_id.id)
        return res

    def action_post(self):
        #rehago la numeración acá porque get_last_secuence trae el último grabado y siempre trae el mismo si hay mas de un
        #movimiento para un journal
        for rec in self:
            if rec.journal_id:
                if not rec.reconciled_bill_ids:
                    rec.move_id.journal_id = rec.journal_id.id
                    last_sequence = rec.move_id._get_last_sequence()
                    new = not last_sequence
                    if new:
                        last_sequence = rec.move_id._get_last_sequence(
                            relaxed=True) or rec.move_id._get_starting_sequence()
                    # Modificación de BIRTUM ya que cuando en los pagos
                    # vienen retenciones el name es '/' por lo que al tratar
                    # de hacer el typecast a int salta un error.
                    last_num = rec.move_id.name[-4:]
                    try:
                        nro_move = int(last_num)
                    except:
                        nro_move = False
                    last_secuence_number = int(last_sequence[-4:])
                    if isinstance(nro_move, int) and last_secuence_number >= nro_move:
                        rec.move_id._set_next_sequence()
                    rec.name = rec.move_id.name
            super(AccountPayment, rec).action_post()
