from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)


MAP_PARTNER_TYPE_ACCOUNT_TYPE = {
    'customer': 'receivable',
    'supplier': 'payable',
}
MAP_ACCOUNT_TYPE_PARTNER_TYPE = {
    'receivable': 'customer',
    'payable': 'supplier',
}


class AccountPaymentGroup(models.Model):
    _name = "account.payment.group"
    _description = "Payment Group"
    _order = "payment_date desc"
    _inherit = 'mail.thread'

    related_invoice = fields.Many2one(comodel_name='account.move',string="Factura Relacionada", readonly=1)
    related_invoice_amount = fields.Monetary(string="Monto Factura", related="related_invoice.amount_total", readonly=1)
    document_number = fields.Char(
        string='Nro Documento',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
    )
    document_sequence_id = fields.Many2one(
        related='receiptbook_id.sequence_id',
    )
    localization = fields.Char('Localizacion', default='argentina')

    receiptbook_id = fields.Many2one(
        'account.payment.receiptbook',
        'Talonario de Recibos',
        readonly=True,
        states={'draft': [('readonly', False)]},
        ondelete='restrict',
        auto_join=True,
    )
    next_number = fields.Integer(
        related='receiptbook_id.sequence_id.number_next_actual',
        string='Prox Numero',
    )
    name = fields.Char(
        compute='_compute_name',
        string='Referencia',
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        index=True,
        change_default=True,
        default=lambda self: self.env.user.company_id,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    payment_methods = fields.Char(
        string='Metodos de Pago',
        compute='_compute_payment_methods',
        search='_search_payment_methods',
    )
    partner_type = fields.Selection(
        [('customer', 'Customer'), ('supplier', 'Vendor')],
        change_default=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente/Proveedor',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        change_default=True,
        index=True,
    )
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    payment_date = fields.Date(
        string='Fecha de Pago',
        default=fields.Date.context_today,
        required=True,
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
    )
    communication = fields.Char(
        string='Memo',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    notes = fields.Text(
        string='Notas'
    )
    matched_amount = fields.Monetary(
        #compute='_compute_matched_amounts',
        currency_field='currency_id',
    )
    unmatched_amount = fields.Monetary(
        #compute='_compute_matched_amounts',
        currency_field='currency_id',
    )
    matched_amount_untaxed = fields.Monetary(
        #compute='_compute_matched_amount_untaxed',
        currency_field='currency_id',
    )
    selected_finacial_debt = fields.Monetary(
        string='Deuda Seleccionada',
        compute='_compute_selected_debt',
    )
    selected_debt = fields.Monetary(
        # string='To Pay lines Amount',
        string='Deuda Seleccionada',
        compute='_compute_selected_debt',
    )
    # this field is to be used by others
    selected_debt_untaxed = fields.Monetary(
        # string='To Pay lines Amount',
        string='Deuda Seleccionada sin Impuestos',
        #string='Selected Debt Untaxed',
        compute='_compute_selected_debt',
    )
    unreconciled_amount = fields.Monetary(
        string='Ajuste / Adelanto',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    # reconciled_amount = fields.Monetary(compute='_compute_amounts')
    to_pay_amount = fields.Monetary(
        compute='_compute_to_pay_amount',
        #inverse='_inverse_to_pay_amount',
        string='Monto a Pagar',
        # string='Total To Pay Amount',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    payments_amount = fields.Monetary(
        compute='_compute_payments_amount',
        string='Monto',
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('posted', 'Publicado'),
        # ('sent', 'Sent'),
        # ('reconciled', 'Reconciled')
        ('cancel', 'Cancelada'),
    ],
        readonly=True,
        default='draft',
        copy=False,
        string="Status",
        index=True,
    )
    move_lines_domain = [
        #('move_id.partner_id.id', '=', partner_id.id),
        # ('account_id.internal_type', '=', account_internal_type),
        ('move_id.state', '=', 'posted'),
        ('account_id.reconcile', '=', True),
        ('reconciled', '=', False),
        ('full_reconcile_id', '=', False),
        # ('company_id', '=', company_id),
    ]
    debt_move_line_ids = fields.Many2many(
        'account.move.line',
        # por alguna razon el related no funciona bien ni con states ni
        # actualiza bien con el onchange, hacemos computado mejor
        compute='_compute_debt_move_line_ids',
        inverse='_inverse_debt_move_line_ids',
        string="Lineas de deuda",
        # no podemos ordenar por due date porque esta hardecodeado en
        # funcion _get_pair_to_reconcile
        help="Payment will be automatically matched with the oldest lines of "
        "this list (by maturity date). You can remove any line you"
        " dont want to be matched.",
        domain=move_lines_domain,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    has_outstanding = fields.Boolean(
        #compute='_compute_has_outstanding',
    )
    to_pay_move_line_ids = fields.Many2many(
        'account.move.line',
        'account_move_line_payment_group_to_pay_rel',
        'payment_group_id',
        'to_pay_line_id',
        string="Lineas a Pagar",
        help='This lines are the ones the user has selected to be paid.',
        copy=False,
        domain=move_lines_domain,
        # lo hacemos readonly por vista y no por aca porque el relatd si no
        # no funcionaba bien
        readonly=True,
        states={'draft': [('readonly', False)]},
        # auto_join not yet implemented for m2m. TODO enable when implemented
        # https://github.com/odoo/odoo/blob/master/odoo/osv/expression.py#L899
        # auto_join=True,
    )
    matched_move_line_ids = fields.Many2many(
        'account.move.line',
        compute='_compute_matched_move_line_ids',
        string='Lineas pagadas',
        help='Lines that has been matched to payments, only available after '
        'payment validation',
    )
    payment_subtype = fields.Char(
        compute='_compute_payment_subtype'
    )
    pop_up = fields.Boolean(
        # campo que agregamos porque el  invisible="context.get('pop_up')"
        # en las pages no se comportaba bien con los attrs
        compute='_compute_payment_pop_up',
        default=lambda x: x._context.get('pop_up', False),
    )
    payment_difference = fields.Monetary(
        compute='_compute_payment_difference',
        # TODO rename field or remove string
        # string='Remaining Residual',
        readonly=True,
        string="Diferencia en los Pagos",
        help="Difference between selected debt (or to pay amount) and "
        "payments amount"
    )
    payment_ids = fields.One2many(
        'account.payment',
        'payment_group_id',
        string='Lineas de Pago',
        copy=False,
        readonly=True,
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', False)]},
        auto_join=True,
    )
    account_internal_type = fields.Char(
        compute='_compute_account_internal_type'
    )
    move_line_ids = fields.Many2many(
        'account.move.line',
        # related o2m a o2m solo toma el primer o2m y le hace o2m, por eso
        # hacemos computed
        # related='payment_ids.move_line_ids',
        compute='_compute_move_lines',
        readonly=True,
        copy=False,
    )
    sent = fields.Boolean(
        readonly=True,
        default=False,
        copy=False,
        help="It indicates that the receipt has been sent."
    )

    num_op = fields.Char('Nº OP Cliente')
    branch_op = fields.Char('Sucursal OP Cliente')


    _sql_constraints = [
        ('document_number_uniq', 'unique(document_number, receiptbook_id)',
            'Document number must be unique per receiptbook!')]

    def _compute_next_number(self):
        """
        show next number only for payments without number and on draft state
        """
        for payment in self.filtered(
            lambda x: x.state == 'draft' and x.receiptbook_id and
                not x.document_number):
            sequence = payment.receiptbook_id.sequence_id
            # we must check if sequence use date ranges
            if not sequence.use_date_range:
                payment.next_number = sequence.number_next_actual
            else:
                dt = self.payment_date or fields.Date.today()
                seq_date = self.env['ir.sequence.date_range'].search([
                    ('sequence_id', '=', sequence.id),
                    ('date_from', '<=', dt),
                    ('date_to', '>=', dt)], limit=1)
                if not seq_date:
                    seq_date = sequence._create_date_range_seq(dt)
                payment.next_number = seq_date.number_next_actual


    @api.depends(
        # 'move_name',
        'state',
        'document_number',
    )
    def _compute_name(self):
        """
        * If document number and document type, we show them
        * Else, we show name
        """
        for rec in self:
            _logger.info('Getting name for payment group %s' % rec.id)
            if rec.state == 'posted':
                if rec.document_number:
                    name = ("%s%s" % ('REC',rec.document_number))
                # for compatibility with v8 migration because receipbook
                # was not required and we dont have a name
                else:
                    name = ', '.join(rec.payment_ids.mapped('name'))
            else:
                name = _('Draft Payment')
            rec.name = name

    _sql_constraints = [
        ('name_uniq', 'unique(document_number, receiptbook_id)',
            'Document number must be unique per receiptbook!')]

    @api.constrains('company_id', 'partner_type')
    def _force_receiptbook(self):
        # we add cosntrins to fix odoo tests and also help in inmpo of data
        for rec in self:
            if not rec.receiptbook_id:
                rec.receiptbook_id = rec._get_receiptbook()

    @api.onchange('company_id', 'partner_type')
    def get_receiptbook(self):
        self.receiptbook_id = self._get_receiptbook()

    def _get_receiptbook(self):
        self.ensure_one()
        partner_type = self.partner_type or self._context.get(
            'partner_type', self._context.get('default_partner_type', False))
        receiptbook = self.env[
            'account.payment.receiptbook'].search([
                ('partner_type', '=', partner_type),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        return receiptbook

    @api.constrains('receiptbook_id', 'company_id')
    def _check_company_id(self):
        """
        Check receiptbook_id and voucher company
        """
        for rec in self:
            if (rec.receiptbook_id and
                    rec.receiptbook_id.company_id != rec.company_id):
                raise ValidationError(_(
                    'The company of the receiptbook and of the '
                    'payment must be the same!'))

    @api.constrains('receiptbook_id', 'document_number')
    def validate_document_number(self):
        for rec in self:
            # if we have a sequence, number is set by sequence and we dont
            # check this
            if rec.document_sequence_id or not rec.document_number \
                    or not rec.receiptbook_id:
                continue
            # para usar el validator deberiamos extenderlo para que reciba
            # el registro o alguna referencia asi podemos obtener la data
            # del prefix y el padding del talonario de recibo
            res = rec.document_number
            padding = rec.receiptbook_id.padding
            res = '{:>0{padding}}'.format(res, padding=padding)

            prefix = rec.receiptbook_id.prefix
            if prefix and not res.startswith(prefix):
                res = prefix + res

            if res != rec.document_number:
                rec.document_number = res


    @api.depends(
        'state',
        'payments_amount',
        'matched_move_line_ids.payment_group_matched_amount')
    def _compute_matched_amounts(self):
        for rec in self:
            if rec.state != 'posted':
                continue
            if not rec.partner_id:
                continue
            # damos vuelta signo porque el payments_amount tmb lo da vuelta,
            # en realidad porque siempre es positivo y se define en funcion
            # a si es pago entrante o saliente
            sign = rec.partner_type == 'supplier' and -1.0 or 1.0
            rec.matched_amount = sign * sum(
                rec.matched_move_line_ids.with_context(
                    payment_group_id=rec.id).mapped(
                        'payment_group_matched_amount'))
            rec.unmatched_amount = rec.payments_amount - rec.matched_amount

    def _compute_matched_amount_untaxed(self):
        """ Lo separamos en otro metodo ya que es un poco mas costoso y no se
        usa en conjunto con matched_amount
        """
        for rec in self:
            if rec.state != 'posted':
                continue
            if not rec.partner_id:
                continue
            matched_amount_untaxed = 0.0
            sign = rec.partner_type == 'supplier' and -1.0 or 1.0
            for line in rec.matched_move_line_ids.with_context(
                    payment_group_id=rec.id):
                #invoice = line.invoice_id
                invoice = line.move_id
                factor = invoice and invoice._get_tax_factor() or 1.0
                matched_amount_untaxed += \
                    line.payment_group_matched_amount * factor
            rec.matched_amount_untaxed = sign * matched_amount_untaxed

    @api.depends('to_pay_move_line_ids')
    def _compute_has_outstanding(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            if rec.partner_type == 'supplier':
                # field = 'debit'
                lines = rec.to_pay_move_line_ids.filtered(
                    lambda x: x.amount_residual > 0.0)
            else:
                lines = rec.to_pay_move_line_ids.filtered(
                    lambda x: x.amount_residual < 0.0)
            if len(lines) != 0:
                rec.has_outstanding = True

    def _search_payment_methods(self, operator, value):
        recs = self.search([('payment_ids.journal_id.name', operator, value)])
        return [('id', 'in', recs.ids)]

    def _compute_payment_methods(self):
        # TODO tal vez sea interesante sumar al string el metodo en si mismo
        # (manual, cheque, etc)

        # tuvmos que hacerlo asi sudo porque si no tenemos error, si agregamos
        # el sudo al self o al rec no se computa el valor, probamos tmb
        # haciendo compute sudo y no anduvo, la unica otra alternativa que
        # funciono es el search de arriba (pero que no muestra todos los
        # names)
        for rec in self:
            # journals = rec.env['account.journal'].search(
            #     [('id', 'in', rec.payment_ids.ids)])
            # rec.payment_methods = ", ".join(journals.mapped('name'))
            rec.payment_methods = ", ".join(rec.payment_ids.sudo().mapped(
                'journal_id.name'))

    def action_payment_sent(self):
        """ Open a window to compose an email, with the edi payment template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref(
            'account_payment_group.email_template_edi_payment_group',
            False)
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.payment.group',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_payment_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def payment_print(self):
        # self.sent = True
        report = self.env['ir.actions.report']._get_report_from_name('account_payment_group.report_payment_group')
        return report.report_action(docids=self)


    @api.depends('to_pay_move_line_ids')
    def _compute_debt_move_line_ids(self):
        for rec in self:
            rec.debt_move_line_ids = rec.to_pay_move_line_ids

    @api.onchange('debt_move_line_ids')
    def _inverse_debt_move_line_ids(self):
        for rec in self:
            rec.to_pay_move_line_ids = rec.debt_move_line_ids

    def _compute_payment_pop_up(self):
        pop_up = self._context.get('pop_up', False)
        for rec in self:
            rec.pop_up = pop_up

    @api.depends('company_id.double_validation', 'partner_type')
    def _compute_payment_subtype(self):
        force_simple = self._context.get('force_simple')
        for rec in self:
            if (rec.partner_type == 'supplier' and
                    rec.company_id.double_validation and not force_simple):
                payment_subtype = 'double_validation'
            else:
                payment_subtype = 'simple'
            rec.payment_subtype = payment_subtype

    def _compute_matched_move_line_ids(self):
        """
        Lar partial reconcile vinculan dos apuntes con credit_move_id y
        debit_move_id.
        Buscamos primeros todas las que tienen en credit_move_id algun apunte
        de los que se genero con un pago, etnonces la contrapartida
        (debit_move_id), son cosas que se pagaron con este pago. Repetimos
        al revz (debit_move_id vs credit_move_id)
        """
        for rec in self:
            lines = rec.move_line_ids.browse()
            # not sure why but self.move_line_ids dont work the same way
            #payment_lines = rec.payment_ids.mapped('move_line_ids')
            payment_lines = rec.payment_ids.mapped('invoice_line_ids')

            reconciles = rec.env['account.partial.reconcile'].search([
                ('credit_move_id', 'in', payment_lines.ids)])
            lines |= reconciles.mapped('debit_move_id')

            reconciles = rec.env['account.partial.reconcile'].search([
                ('debit_move_id', 'in', payment_lines.ids)])
            lines |= reconciles.mapped('credit_move_id')

            rec.matched_move_line_ids = lines - payment_lines

    # @api.depends('payment_ids.move_line_ids')
    @api.depends('payment_ids.invoice_line_ids')
    def _compute_move_lines(self):
        for rec in self:
            rec.move_line_ids = rec.payment_ids.mapped('invoice_line_ids')

    @api.depends('partner_type')
    def _compute_account_internal_type(self):
        for rec in self:
            if rec.partner_type:
                rec.account_internal_type = MAP_PARTNER_TYPE_ACCOUNT_TYPE[
                    rec.partner_type]

    def _compute_payment_difference(self):
        for rec in self:
            # if rec.payment_subtype != 'double_validation':
            #     continue
            rec.payment_difference = rec.to_pay_amount - rec.payments_amount

    @api.depends('payment_ids.signed_amount_company_currency')
    def _compute_payments_amount(self):
        for rec in self:
            rec.payments_amount = sum(rec.payment_ids.mapped(
                'signed_amount_company_currency'))
            # payments_amount = sum([
            #     x.payment_type == 'inbound' and
            #     x.amount_company_currency or -x.amount_company_currency for
            #     x in rec.payment_ids])
            # rec.payments_amount = (
            #     rec.partner_type == 'supplier' and
            #     -payments_amount or payments_amount)

    def _compute_selected_debt(self):
        for rec in self:
            selected_finacial_debt = 0.0
            selected_debt = 0.0
            selected_debt_untaxed = 0.0
            for line in rec.debt_move_line_ids:
                selected_finacial_debt += line.financial_amount_residual
                selected_debt += line.amount_residual
                # factor for total_untaxed
                invoice = line.move_id
                factor = invoice and invoice._get_tax_factor() or 1.0
                selected_debt_untaxed += line.amount_residual * factor
            sign = rec.partner_type == 'supplier' and -1.0 or 1.0
            rec.selected_finacial_debt = selected_finacial_debt * sign
            rec.selected_debt = selected_debt * sign
            rec.selected_debt_untaxed = selected_debt_untaxed * sign

    #@api.depends(
    #    'selected_debt', 'unreconciled_amount')
    def _compute_to_pay_amount(self):
        for rec in self:
            rec.to_pay_amount = rec.selected_debt + rec.unreconciled_amount

    @api.onchange('to_pay_amount')
    def _inverse_to_pay_amount(self):
        for rec in self:
            rec.unreconciled_amount = rec.to_pay_amount - rec.selected_debt

    @api.onchange('partner_id', 'partner_type', 'company_id')
    def _refresh_payments_and_move_lines(self):
        # clean actual invoice and payments
        # no hace falta
        if self._context.get('pop_up'):
            return
        for rec in self:
            rec.payment_ids = [(2, item.id, 0) for item in rec.payment_ids]
            rec.add_all()

    def onchange(self, values, field_name, field_onchange):
        """Necesitamos hacer esto porque los onchange que agregan lineas,
        cuando se va a guardar el registro, terminan creando registros.
        """
        fields = []
        for field in field_onchange.keys():
            if field.startswith((
                    'to_pay_move_line_ids.',
                    'debt_move_line_ids.')):
                fields.append(field)
        for field in fields:
            del field_onchange[field]
        return super(AccountPaymentGroup, self).onchange(
            values, field_name, field_onchange)

    def _get_to_pay_move_lines_domain(self):
        self.ensure_one()
        return [
            ('partner_id.commercial_partner_id', '=',
                self.commercial_partner_id.id),
            ('account_id.internal_type', '=',
                self.account_internal_type),
            ('account_id.reconcile', '=', True),
            ('move_id.move_type', 'in', ['out_invoice','out_refund','in_invoice','in_refund']),
            ('reconciled', '=', False),
            ('full_reconcile_id', '=', False),
            ('company_id', '=', self.company_id.id),
            # '|',
            # ('amount_residual', '!=', False),
            # ('amount_residual_currency', '!=', False),
        ]

    def add_all(self):
        for rec in self:
            rec.to_pay_move_line_ids = rec.env['account.move.line'].search(
                rec._get_to_pay_move_lines_domain())

    def remove_all(self):
        self.to_pay_move_line_ids = False

    @api.model
    def default_get(self, fields):
        rec = super(AccountPaymentGroup, self).default_get(fields)
        to_pay_move_line_ids = self._context.get('to_pay_move_line_ids')
        to_pay_move_lines = self.env['account.move.line'].browse(
            to_pay_move_line_ids).filtered(lambda x: (
                x.account_id.reconcile and
                x.account_id.internal_type in ('receivable', 'payable')))

        if self._context.get('from_invoice') == 'yes':
            invoice = self.env['account.move'].browse(self._context.get('invoice_id'))
            rec['related_invoice'] = invoice.id
            
            if self.env['ir.config_parameter'].get_param('account_payment_group.journal_def'):

                payment_type = ''
                partner_type = ''
                if invoice.move_type == 'out_invoice' or invoice.move_type == 'out_refund' or invoice.move_type == 'out_receipt':
                    payment_type = 'inbound'
                    partner_type = 'customer'
                else:
                    payment_type = 'outbound'
                    partner_type = 'supplier'

                rec['payment_ids'] = [(0, 0, {'payment_group_id': self.id,
                                                'state': 'draft',
                                                'partner_type': partner_type,
                                                'payment_type': payment_type,
                                                'journal_id': int(self.env['ir.config_parameter'].get_param('account_payment_group.journal_def')) or False,
                                                'amount': self._context.get('amount_invoice')})]

        if to_pay_move_lines:
            partner = to_pay_move_lines.mapped('partner_id')
            if len(partner) != 1:
                raise ValidationError(_(
                    'No se pueden mandar líneas de pagos a diferentes Contactos'))

            internal_type = to_pay_move_lines.mapped(
                'account_id.internal_type')
            if len(internal_type) != 1:
                raise ValidationError(_(
                    'No se pueden mandar líneas de pagos desde diferentes Contactos'))
            rec['partner_id'] = self._context.get(
                'default_partner_id', partner[0].id)
            partner_id = self._context.get('default_partner_id',partner[0].id)
            if partner_id:
                if type(partner_id) == int:
                    partner_id = self.env['res.partner'].browse(partner_id)
                if partner_id.customer_rank:
                    rec['partner_type'] = 'customer'
                if partner_id.supplier_rank:
                    rec['partner_type'] = 'supplier'
            rec['to_pay_move_line_ids'] = [(6, False, to_pay_move_line_ids)]

        return rec

    def button_journal_entries(self):
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('payment_id', 'in', self.payment_ids.ids)],
        }

    def unreconcile(self):
        for rec in self:
            rec.payment_ids.unreconcile()
        # TODO en alguos casos setear sent como en payment?
        self.write({'state': 'posted'})

    def cancel(self):
        for rec in self:
            # because child payments dont have invoices we remove reconcile
            for move in rec.move_line_ids.mapped('move_id'):
                rec.matched_move_line_ids.remove_move_reconcile()
                # TODO borrar esto si con el de arriba va bien
                # if rec.to_pay_move_line_ids:
                #     move.line_ids.remove_move_reconcile()
            rec.payment_ids.action_cancel()
            rec.payment_ids.write({'invoice_line_ids': [(5, 0, 0)]})
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.mapped('payment_ids').action_draft()
        return self.write({'state': 'draft'})

    def unlink(self):
        if any(rec.state != 'draft' for rec in self):
            raise ValidationError(_(
                "You can not delete a payment that is already posted"))
        return super(AccountPaymentGroup, self).unlink()

    def confirm(self):
        for rec in self:
            accounts = rec.to_pay_move_line_ids.mapped('account_id')
            if len(accounts) > 1:
                raise ValidationError(_(
                    'To Pay Lines must be of the same account!'))
        self.write({'state': 'confirmed'})

    def post(self):
        # dont know yet why, but if we came from an invoice context values
        # break behaviour, for eg. with demo user error writing account.account
        # and with other users, error with block date of accounting
        # TODO we should look for a better way to solve this

        create_from_website = self._context.get(
            'create_from_website', False)
        create_from_statement = self._context.get(
            'create_from_statement', False)
        create_from_expense = self._context.get('create_from_expense', False)
        self = self.with_context({})
        for rec in self:
            _logger.warning("entro")
            if not rec.receiptbook_id:
                rec.payment_ids.write({
                    'receiptbook_id': False,
                })
                continue
            
            _logger.warning("2")
            if not rec.document_number:
                if not rec.receiptbook_id.sequence_id:
                    raise UserError(_(
                        'Error!. Please define sequence on the receiptbook'
                        ' related documents to this payment or set the '
                        'document number.'))
                rec.document_number = (
                    rec.receiptbook_id.with_context(
                        ir_sequence_date=rec.payment_date
                        ).sequence_id.next_by_id())
            #rec.payment_ids.write({
            #    'document_number': rec.document_number,
            #    'receiptbook_id': rec.receiptbook_id.id,
            #})

            _logger.warning("3")
            # TODO if we want to allow writeoff then we can disable this
            # constrain and send writeoff_journal_id and writeoff_acc_id
            if not rec.payment_ids:
                raise ValidationError(_(
                    'You can not confirm a payment group without payment '
                    'lines!'))
            # si el pago se esta posteando desde statements y hay doble
            # validacion no verificamos que haya deuda seleccionada
            _logger.warning("4")
            if (rec.payment_subtype == 'double_validation' and
                    rec.payment_difference and (not create_from_statement and
                                                not create_from_expense)):
                raise ValidationError(_(
                    'To Pay Amount and Payment Amount must be equal!'))

            writeoff_acc_id = False
            writeoff_journal_id = False

            # al crear desde website odoo crea primero el pago y lo postea
            # y no debemos re-postearlo
            if not create_from_website and not create_from_expense:
                rec.payment_ids.filtered(lambda x: x.state == 'draft').action_post()

            #counterpart_aml = rec.payment_ids.mapped('move_line_ids').filtered(
            counterpart_aml = rec.payment_ids.mapped('invoice_line_ids').filtered(
                lambda r: not r.reconciled and r.account_id.internal_type in (
                    'payable', 'receivable'))

            # porque la cuenta podria ser no recivible y ni conciliable
            # (por ejemplo en sipreco)
            if counterpart_aml and rec.to_pay_move_line_ids:
                #(counterpart_aml + (rec.to_pay_move_line_ids)).reconcile(
                #    writeoff_acc_id, writeoff_journal_id)
                (counterpart_aml + (rec.to_pay_move_line_ids)).reconcile()

            rec.state = 'posted'
            if rec.receiptbook_id.mail_template_id:
                rec.message_post_with_template(
                    rec.receiptbook_id.mail_template_id.id,
                )


    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_payment_as_sent'):
            self.filtered(lambda rec: not rec.sent).write({'sent': True})
        return super(AccountPaymentGroup, self.with_context(
            mail_post_autofollow=True)).message_post(**kwargs)
