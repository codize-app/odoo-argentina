##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import datetime
import logging
_logger = logging.getLogger(__name__)


class AccountCheckOperation(models.Model):

    _name = 'account.check.operation'
    _description = 'account.check.operation'
    _rec_name = 'operation'
    _order = 'date desc, id desc'

    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
        index=True,
    )
    check_id = fields.Many2one(
        'account.check',
        'Cheque',
        required=True,
        ondelete='cascade',
        auto_join=True,
        index=True,
    )
    operation = fields.Selection([
        # from payments
        ('holding', 'Recibir'),
        ('deposited', 'Depositar'),
        ('selled', 'Vender'),
        ('delivered', 'Entregar'),
        # usado para hacer transferencias internas, es lo mismo que delivered
        # (endosado) pero no queremos confundir con terminos, a la larga lo
        # volvemos a poner en holding
        ('transfered', 'Transferir'),
        ('handed', 'En mano'),
        ('withdrawed', 'Retiro'),
        # from checks
        ('reclaimed', 'Reclamar'),
        ('rejected', 'Rechazar'),
        ('debited', 'Debitar'),
        ('returned', 'Retornar'),
        # al final no vamos a implemnetar esto ya que habria que hacer muchas
        # cosas hasta actualizar el asiento, mejor se vuelve atras y se
        # vuelve a generar deuda y listo, igualmente lo dejamos por si se
        # quiere usar de manera manual
        ('changed', 'Cambiar'),
        ('cancel', 'Cancelar'),
    ],
        required=True,
        index=True,
    )
    origin_name = fields.Char(
        compute='_compute_origin_name'
    )
    origin = fields.Reference(
        string='Origen',
        selection='_reference_models')
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente/Proveedor',
    )
    notes = fields.Text()

    def unlink(self):
        for rec in self:
            if rec.origin:
                raise ValidationError(_(
                    'You can not delete a check operation that has an origin.'
                    '\nYou can delete the origin reference and unlink after.'))
        return super(AccountCheckOperation, self).unlink()

    @api.depends('origin')
    def _compute_origin_name(self):
        """
        We add this computed method because an error on tree view displaying
        reference field when destiny record is deleted.
        As said in this post (last answer) we should use name_get instead of
        display_name
        https://www.odoo.com/es_ES/forum/ayuda-1/question/
        how-to-override-name-get-method-in-new-api-61228
        """
        for rec in self:
            try:
                if rec.origin:
                    _id, name = rec.origin.name_get()[0]
                    origin_name = name
                    # origin_name = rec.origin.display_name
                else:
                    origin_name = False
            except Exception as e:
                _logger.exception(
                    "Compute origin on checks exception: %s" % e)
                # if we can get origin we clean it
                rec.write({'origin': False})
                origin_name = False
            rec.origin_name = origin_name

    @api.model
    def _reference_models(self):
        return [
            ('account.payment', 'Pago'),
            ('account.check', 'Cheque'),
            ('account.move', 'Asiento Contable'),
            ('account.move.line', 'Apunte Contable'),
            ('account.bank.statement.line', 'Línea de Declaración'),
        ]

class AccountCheck(models.Model):

    _name = 'account.check'
    _description = 'Account Check'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    operation_ids = fields.One2many(
        'account.check.operation',
        'check_id',
        auto_join=True,
    )
    name = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
        index=True,
    )
    number = fields.Integer(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        index=True,
    )
    checkbook_id = fields.Many2one(
        'account.checkbook',
        'Recibos',
        readonly=True,
        states={'draft': [('readonly', False)]},
        auto_join=True,
        index=True,
    )
    issue_check_subtype = fields.Selection(
        related='checkbook_id.issue_check_subtype',
    )
    type = fields.Selection(
        [('issue_check', 'Cheque Emitido'), ('third_check', 'Cheque de Terceros')],
        readonly=True,
        index=True,
    )
    partner_id = fields.Many2one(
        related='operation_ids.partner_id',
        store=True,
        index=True,
        string='Last operation partner',
    )
    first_partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_first_partner',
        string='First operation partner',
        readonly=True,
        #store=True,
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('holding', 'En Mano'),
        ('deposited', 'Depositado'),
        ('selled', 'Vendido'),
        ('delivered', 'Entregado'),
        ('transfered', 'Transferido'),
        ('reclaimed', 'Reclamado'),
        ('withdrawed', 'Retirado'),
        ('handed', 'Handed'),
        ('rejected', 'Rechazado'),
        ('debited', 'Debitado'),
        ('returned', 'Retornado'),
        ('changed', 'Cambiado'),
        ('cancel', 'Cancelado'),
    ],
        required=True,
        default='draft',
        copy=False,
        compute='_compute_state',
        store=True,
        index=True,
    )
    issue_date = fields.Date(
        'Fecha Emision',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today,
    )
    owner_vat = fields.Char(
        'CUIT del Emisor',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    owner_name = fields.Char(
        'Emisor',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    bank_id = fields.Many2one(
        'res.bank', 'Banco',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    amount = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    amount_company_currency = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    currency_id = fields.Many2one(
        'res.currency',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user.company_id.currency_id.id,
        required=True,
    )
    payment_date = fields.Date(
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        required=True,
        domain=[('type', 'in', ['cash', 'bank'])],
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
    )
    company_id = fields.Many2one(
        related='journal_id.company_id',
        store=True,
    )
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Moneda de la empresa',
    )

    def back_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def op_clean(self):
        for rec in self:
            rec.operation_ids = False

    def get_bank_vals(self, action, journal):
        self.ensure_one()
        # TODO improove how we get vals, get them in other functions
        if action == 'bank_debit':
            # self.journal_id.default_debit_account_id.id, al debitar
            # tenemos que usar esa misma
            credit_account = journal.default_account_id
            debit_account = self.company_id._get_check_account('deferred')
            if self.type == 'third_check':
                if journal.account_third:
                    debit_account = journal.account_third
            else:
                if journal.account_holding:
                    credit_account = journal.account_holding
                    debit_account = self.company_id._get_check_account('deferred')
            name = _('Check "%s" debit') % (self.name)
        elif action == 'bank_reject':
            # al transferir a un banco se usa esta. al volver tiene que volver
            # por la opuesta
            # self.destination_journal_id.default_credit_account_id
            credit_account = journal.default_account_id
            debit_account = self.company_id._get_check_account('rejected')
            name = _('Check "%s" rejection') % (self.name)
        elif action == 'bank_deposit' or action == 'bank_sell':
            # al transferir a un banco se usa esta. al volver tiene que volver
            # por la opuesta
            # self.destination_journal_id.default_credit_account_id
            name = _('Check "%s" deposit') % (self.name)
            if action == 'bank_deposit':
                  debit_account = journal.default_account_id
                  credit_account = self.company_id._get_check_account('holding')
                  if self.type == 'third_check':
                      if journal.account_third:
                          debit_account = journal.account_third
                  else:
                      if journal.account_holding:
                          debit_account = journal.account_holding
            if action == 'bank_sell' and not self.company_id.negotiated_check_account_id:
                  raise ValidationError('No esta definida la cuenta de cheques negociados a nivel empresa')
            if action == 'bank_sell':
                  debit_account = self.company_id.negotiated_check_account_id
                  credit_account = self.company_id._get_check_account('holding')
                  if not credit_account:
                        raise ValidationError('Falta la cuenta holding_check_account_id')
                  if not debit_account:
                        raise ValidationError('Falta la cuenta negotiated_check_account_id')
                  if action == 'bank_deposit':
                        name = _('Check "%s" deposit') % (self.name)
                  else:
                        name = _('Check "%s" sell') % (self.name)
        else:
            raise ValidationError(_(
                                'Action %s not implemented for checks!') % action)
        if self.currency_id.id != self.company_id.currency_id.id:
            currency_id = self.company_id.currency_id
            amount_currency = 0
            amount = self.amount * self.currency_rate
        else:
            currency_id = self.currency_id
            amount = self.amount
            amount_currency = self.amount_company_currency
        debit_line_vals = {
            'name': name,
            'account_id': debit_account.id,
            # 'partner_id': partner,
            'debit': amount,
            'amount_currency': amount_currency,
            #'currency_id': currency_id.id,
            # 'ref': ref,
            }
        credit_line_vals = {
            'name': name,
            'account_id': credit_account.id,
            # 'partner_id': partner,
            'credit': amount,
            'amount_currency': amount_currency * -1,
            #'currency_id': currency_id.id,
            # 'ref': ref,
            }

        return {
               'ref': name,
               'journal_id': journal.id,
               'date': fields.Date.today(),
               'line_ids': [
                   (0, False, debit_line_vals),
                   (0, False, credit_line_vals)],
               }

    @api.depends('operation_ids.partner_id')
    def _compute_first_partner(self):
        for rec in self:
            if rec.operation_ids:
                if rec.operation_ids[-1].partner_id:
                    rec.first_partner_id = rec.operation_ids[-1].partner_id
                else:
                    rec.first_partner_id = None
            else:
                rec.first_partner_id = None

    def onchange(self, values, field_name, field_onchange):
        """
        Con esto arreglamos el borrador del origin de una operacíón de deposito
        (al menos depositos de v8 migrados), habría que ver si pasa en otros
        casos y hay algo más que arreglar
        # TODO si no pasa en v11 borrarlo
        """
        'operation_ids.origin' in field_onchange and field_onchange.pop(
            'operation_ids.origin')
        return super(AccountCheck, self).onchange(
            values, field_name, field_onchange)

    @api.constrains('issue_date', 'payment_date')
    @api.onchange('issue_date', 'payment_date')
    def onchange_date(self):
        for rec in self:
            if (
                    rec.issue_date and rec.payment_date and
                    rec.issue_date > rec.payment_date):
                raise UserError(
                    _('Check Payment Date must be greater than Issue Date'))

    @api.constrains(
        'type',
        'number',
    )
    def issue_number_interval(self):
        for rec in self:
            # if not range, then we dont check it
            if rec.type == 'issue_check' and rec.checkbook_id.range_to:
                if rec.number > rec.checkbook_id.range_to:
                    raise UserError(_(
                        "Check number (%s) can't be greater than %s on "
                        "checkbook %s (%s)") % (
                        rec.number,
                        rec.checkbook_id.range_to,
                        rec.checkbook_id.name,
                        rec.checkbook_id.id,
                    ))
                elif rec.number == rec.checkbook_id.range_to:
                    rec.checkbook_id.state = 'used'
        return False

    @api.constrains(
        'type',
        'owner_name',
        'bank_id',
    )
    def _check_unique(self):
        for rec in self:
            if rec.type == 'issue_check':
                same_checks = self.search([
                    ('checkbook_id', '=', rec.checkbook_id.id),
                    ('type', '=', rec.type),
                    ('number', '=', rec.number),
                ])
                same_checks -= self
                if same_checks:
                    raise ValidationError(_(
                        'Check Number (%s) must be unique per Checkbook!\n'
                        '* Check ids: %s') % (
                        rec.name, same_checks.ids))
            elif self.type == 'third_check':
                # agregamos condicion de company ya que un cheque de terceros
                # se puede pasar entre distintas cias
                same_checks = self.search([
                    ('company_id', '=', rec.company_id.id),
                    ('bank_id', '=', rec.bank_id.id),
                    ('owner_name', '=', rec.owner_name),
                    ('type', '=', rec.type),
                    ('number', '=', rec.number),
                ])
                same_checks -= self
                if same_checks:
                    raise ValidationError(_(
                        'Check Number (%s) must be unique per Owner and Bank!'
                        '\n* Check ids: %s') % (
                        rec.name, same_checks.ids))
        return True

    def _del_operation(self, origin):
        """
        We check that the operation that is being cancel is the last operation
        done (same as check state)
        """
        for rec in self:
            if not rec.operation_ids or rec.operation_ids[0].origin != origin:
                raise ValidationError(_(
                    'You can not cancel this operation because this is not '
                    'the last operation over the check.\nCheck (id): %s (%s)'
                ) % (rec.name, rec.id))
            rec.operation_ids[0].origin = False
            rec.operation_ids[0].unlink()

    def _add_operation(
            self, operation, origin, partner=None, date=False):
        for rec in self:
            rec._check_state_change(operation)
            # agregamos validacion de fechas
            date = date or fields.Datetime.now()
            if type(date) == str:
                date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            if rec.operation_ids and rec.operation_ids[0].date > date:
                raise ValidationError(_(
                    'The date of a new check operation can not be minor than '
                    'last operation date.\n'
                    '* Check Id: %s\n'
                    '* Check Number: %s\n'
                    '* Operation: %s\n'
                    '* Operation Date: %s\n'
                    '* Last Operation Date: %s') % (
                    rec.id, rec.name, operation, date,
                    rec.operation_ids[0].date))
            vals = {
                'operation': operation,
                'date': date,
                'check_id': rec.id,
                'origin': '%s,%i' % (origin._name, origin.id),
                'partner_id': partner and partner.id or False,
            }
            rec.operation_ids.create(vals)

    @api.depends(
        'operation_ids.operation',
        'operation_ids.date',
    )
    def _compute_state(self):
        for rec in self:
            if rec.operation_ids.sorted():
                operation = rec.operation_ids.sorted()[0].operation
                rec.state = operation
            else:
                rec.state = 'draft'

    def _check_state_change(self, operation):
        """
        We only check state change from _add_operation because we want to
        leave the user the possibility of making anything from interface.
        Necesitamos este chequeo para evitar, por ejemplo, que un cheque se
        agregue dos veces en un pago y luego al confirmar se entregue dos veces
        On operation_from_state_map dictionary:
        * key is 'to state'
        * value is 'from states'
        """
        self.ensure_one()
        # if we do it from _add_operation only, not from a contraint of before
        # computing the value, we can just read it
        old_state = self.state
        operation_from_state_map = {
            # 'draft': [False],
            'holding': [
                'draft', 'deposited', 'selled', 'delivered', 'transfered'],
            'delivered': ['holding','rejected'],
            'deposited': ['holding', 'rejected'],
            'selled': ['holding'],
            'handed': ['draft'],
            'transfered': ['holding'],
            'withdrawed': ['draft'],
            'rejected': ['delivered', 'deposited', 'selled', 'handed','rejected'],
            'debited': ['handed'],
            'returned': ['handed', 'holding'],
            'changed': ['handed', 'holding'],
            'cancel': ['draft'],
            'reclaimed': ['rejected'],
        }
        from_states = operation_from_state_map.get(operation)
        if not from_states:
            raise ValidationError(_(
                'Operation %s not implemented for checks!') % operation)
        if old_state not in from_states:
            raise ValidationError(_(
                'You can not "%s" a check from state "%s"!\n'
                'Check nbr (id): %s (%s)') % (
                    self.operation_ids._fields['operation'].convert_to_export(
                        operation, self),
                    self._fields['state'].convert_to_export(old_state, self),
                    self.name,
                    self.id))

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise ValidationError(_(
                    'The Check must be in draft state for unlink !'))
        return super(AccountCheck, self).unlink()

# checks operations from checks


    def bank_deposit(self,date=None,journal_id=None):
        self.ensure_one()
        if self.state in ['holding']:
            if not journal_id:
                raise ValidationError('Debe seleccionar el diario')
            vals = self.get_bank_vals('bank_deposit', journal_id)
            action_date = self._context.get('action_date')
            if not date:
                vals['date'] = action_date or fields.Date.today()
            else:
                vals['date'] = str(date)
            move = self.env['account.move'].create(vals)
            move.action_post()
            self._add_operation('deposited', move, date=vals['date'])
            self.write({'state': 'deposited'})


    def deliver(self):
        self.ensure_one()
        if self.state in ['holding']:
            self.write({'state': 'delivered'})


    def bank_debit(self):
        self.ensure_one()
        if self.state in ['handed']:
            #payment_values = self.get_payment_values(self.journal_id)
            #payment = self.env['account.payment'].with_context(
            #    default_name=_('Check "%s" debit') % (self.name),
            #    force_account_id=self.company_id._get_check_account(
            #        'deferred').id,
            #).create(payment_values)
            #self.post_payment_check(payment)
            #payment.post()
            if not self.operation_ids[0].origin:
                raise ValidationError('La Operación debe tener un Origen')
            journal_id = self.operation_ids[0].origin.journal_id
            if not journal_id:
                raise ValidationError('No puedo determinar el diario de deposito')
            vals = self.get_bank_vals('bank_debit', journal_id)
            action_date = self._context.get('action_date')
            if not action_date:
                vals['date'] = action_date or fields.Date.today()
            else:
                vals['date'] = str(action_date)
            move = self.env['account.move'].create(vals)
            move.action_post()
            #self._add_operation('deposited', move, date=vals['date'])
            #self.handed_reconcile(payment.move_line_ids.mapped('move_id'))
            self._add_operation('debited', move, date=move.date)
            self.state = 'debited'

    @api.model
    def post_payment_check(self, payment):
        """ No usamos post() porque no puede obtener secuencia, hacemos
        parecido a los statements donde odoo ya lo genera posteado
        """
        # payment.post()
        move = payment._create_payment_entry(payment.amount)
        payment.write({'state': 'posted', 'move_name': move.name})

    def handed_reconcile(self, move):
        """
        Funcion que por ahora solo intenta conciliar cheques propios entregados
        cuando se hace un debito o cuando el proveedor lo rechaza
        """

        self.ensure_one()
        debit_account = self.company_id._get_check_account('deferred')

        # conciliamos
        if debit_account.reconcile:
            operation = self._get_operation('handed')
            if operation.origin._name == 'account.payment':
                move_lines = operation.origin.move_line_ids
            elif operation.origin._name == 'account.move':
                move_lines = operation.origin.line_ids
            move_lines |= move.line_ids
            move_lines = move_lines.filtered(
                lambda x: x.account_id == debit_account)
            if len(move_lines) != 2:
                raise ValidationError(_(
                    'We have found more or less than two journal items to '
                    'reconcile with check debit.\n'
                    '*Journal items: %s') % move_lines.ids)
            move_lines.reconcile()

    @api.model
    def get_third_check_account(self):
        """
        For third checks, if we use a journal only for third checks, we use
        accounts on journal, if not we use company account
        # TODO la idea es depreciar esto y que si se usa cheques de terceros
        se use la misma cuenta que la del diario y no la cuenta configurada en
        la cia, lo dejamos por ahora por nosotros y 4 clientes que estan asi
        (cro, ncool, bog).
        Esto era cuando permitíamos o usabamos diario de efectivo con cash y
        cheques
        """
        # self.ensure_one()
        # desde los pagos, pueden venir mas de un cheque pero para que
        # funcione bien, todos los cheques deberian usar la misma cuenta,
        # hacemos esa verificación
        account = self.env['account.account']
        for rec in self:
            #credit_account = rec.journal_id.default_credit_account_id
            #debit_account = rec.journal_id.default_debit_account_id
            debit_account = credit_account = rec.company_id._get_check_account('holding')
            inbound_methods = rec.journal_id['inbound_payment_method_ids']
            outbound_methods = rec.journal_id['outbound_payment_method_ids']
            # si hay cuenta en diario y son iguales, y si los metodos de pago
            # y cobro son solamente uno, usamos el del diario, si no, usamos el
            # de la compañía
            if credit_account and credit_account == debit_account and len(
                    inbound_methods) == 1 and len(outbound_methods) == 1:
                account |= credit_account
            else:
                account |= rec.company_id._get_check_account('holding')
        if len(account) != 1:
            raise ValidationError(_('Error not specified'))
        return account

    @api.model
    def _get_checks_to_date_on_state(self, state, date, force_domain=None):
        """
        Devuelve el listado de cheques que a la fecha definida se encontraban
        en el estadao definido.
        Esta función no la usamos en este módulo pero si en otros que lo
        extienden
        La funcion devuelve un listado de las operaciones a traves de las
        cuales se puede acceder al cheque, devolvemos las operaciones porque
        dan información util de fecha, partner y demas
        """
        # buscamos operaciones anteriores a la fecha que definan este estado
        if not force_domain:
            force_domain = []

        operations = self.operation_ids.search([
            ('date', '<=', date),
            ('operation', '=', state)] + force_domain)

        for operation in operations:
            # buscamos si hay alguna otra operacion posterior para el cheque
            newer_op = operation.search([
                ('date', '<=', date),
                ('id', '>', operation.id),
                ('check_id', '=', operation.check_id.id),
            ])
            # si hay una operacion posterior borramos la op del cheque porque
            # hubo otra operación antes de la fecha
            if newer_op:
                operations -= operation
        return operations

    def _get_operation(self, operation, partner_required=False):
        self.ensure_one()
        op = self.operation_ids.search([
            ('check_id', '=', self.id), ('operation', '=', operation)],
            limit=1)
        if partner_required:
            if not op.partner_id:
                raise ValidationError(_(
                    'The %s (id %s) operation has no partner linked.'
                    'You will need to do it manually.') % (operation, op.id))
        return op

    def claim(self):
        self.ensure_one()
        if self.state in ['rejected'] and self.type == 'third_check':
            # anulamos la operación en la que lo recibimos
            return self.action_create_debit_note(
                'reclaimed', 'customer', self.first_partner_id,
                self.company_id._get_check_account('rejected'))

    def customer_return(self):
        self.ensure_one()
        if self.state in ['holding'] and self.type == 'third_check':
            return self.action_create_debit_note(
                'returned', 'customer', self.first_partner_id,
                self.get_third_check_account())

    @api.model
    def get_payment_values(self, journal):
        """ return dictionary with the values to create the reject check
        payment record.
        We create an outbound payment instead of a transfer because:
        1. It is easier to inherit
        2. Outbound payment withot partner type and partner is not seen by user
        and we don't want to confuse them with this payments
        """
        action_date = self._context.get('action_date', fields.Date.today())
        return {
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'journal_id': journal.id,
            'date': action_date,
            'payment_type': 'outbound',
            'payment_method_id':
            journal._default_outbound_payment_methods().id,
            # 'check_ids': [(4, self.id, False)],
        }

    @api.constrains('currency_id', 'amount', 'amount_company_currency')
    def _check_amounts(self):
        for rec in self.filtered(
                lambda x: not x.amount or not x.amount_company_currency):
            if rec.currency_id != rec.company_currency_id:
                raise ValidationError(_(
                    'If you create a check with different currency thant the '
                    'company currency, you must provide "Amount" and "Amount '
                    'Company Currency"'))
            elif not rec.amount:
                if not rec.amount_company_currency:
                    raise ValidationError(_(
                        'No puede crear un cheque sin importe'))
                rec.amount = rec.amount_company_currency
            elif not rec.amount_company_currency:
                rec.amount_company_currency = rec.amount

    def reject(self):
        self.ensure_one()
        if self.state in ['deposited', 'selled']:
            operation = self._get_operation(self.state)
            if operation.origin._name == 'account.payment':
                journal = operation.origin.destination_journal_id
            # for compatibility with migration from v8
            elif operation.origin._name == 'account.move':
                journal = operation.origin.journal_id
            else:
                raise ValidationError(_(
                    'The deposit operation is not linked to a payment.'
                    'If you want to reject you need to do it manually.'))
            payment_vals = self.get_payment_values(journal)
            payment = self.env['account.payment'].with_context(
                default_name=_('Check "%s" rejection') % (self.name),
                #force_account_id=self.company_id._get_check_account(
                #    'rejected').id,
            ).create(payment_vals)
            # self.post_payment_check(payment)
            self._add_operation('rejected', payment, date=payment.payment_date)
            self.state = 'rejected'
        elif self.state == 'delivered':
            raise ValidationError('accion no implementada')
            operation = self._get_operation(self.state, True)
            self.write({'state': 'rejected'})
            res = self.action_create_debit_note(
                'rejected', 'supplier', operation.partner_id,
                self.company_id._get_check_account('rejected'))
        elif self.state == 'handed':
            operation = self._get_operation(self.state, True)
            return self.action_create_debit_note(
                'rejected', 'supplier', operation.partner_id,
                self.company_id._get_check_account('deferred'))

    def action_create_debit_note(
            self, operation, partner_type, partner, account):
        self.ensure_one()
        action_date = self._context.get('action_date')

        if partner_type == 'supplier':
            invoice_type = 'in_invoice'
            journal_type = 'purchase'
            view_id = self.env.ref('account.view_move_form').id
        else:
            invoice_type = 'out_invoice'
            journal_type = 'sale'
            view_id = self.env.ref('account.view_move_form').id

        journal = self.env['account.journal'].search([
            ('company_id', '=', self.company_id.id),
            ('type', '=', journal_type),
        ], limit=1)

        # si pedimos rejected o reclamo, devolvemos mensaje de rechazo y cuenta
        # de rechazo
        if operation in ['rejected', 'reclaimed']:
            name = 'Rechazo cheque "%s"' % (self.name)
        # si pedimos la de holding es una devolucion
        elif operation == 'returned':
            name = 'Devolución cheque "%s"' % (self.name)
        else:
            raise ValidationError(_(
                'Debit note for operation %s not implemented!' % (
                    operation)))

        inv_line_vals = {
            # 'product_id': self.product_id.id,
            'name': name,
            'account_id': account.id,
            'price_unit': self.amount,
            # 'invoice_id': invoice.id,
        }

        inv_vals = {
            # this is the reference that goes on account.move.line of debt line
            # 'name': name,
            # this is the reference that goes on account.move
            'rejected_check_id': self.id,
            #'ref': name,
            'invoice_date': action_date,
            'ref': _('Check nbr (id): %s (%s)') % (self.name, self.id),
            'journal_id': journal.id,
            # this is done on muticompany fix
            # 'company_id': journal.company_id.id,
            'partner_id': partner.id,
            'move_type': invoice_type,
            'invoice_line_ids': [(0, 0, inv_line_vals)],
        }
        if self.currency_id:
            inv_vals['currency_id'] = self.currency_id.id
        # we send internal_type for compatibility with account_document
        invoice = self.env['account.move'].with_context(
            internal_type='debit_note').create(inv_vals)
        self._add_operation(operation, invoice, partner, date=action_date)

        return {
            'name': name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': view_id,
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
        }
