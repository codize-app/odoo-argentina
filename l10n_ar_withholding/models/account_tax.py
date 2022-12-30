# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from ast import literal_eval
from odoo.tools.safe_eval import safe_eval as eval
from dateutil.relativedelta import relativedelta
import datetime
from datetime import date
import logging
_logger = logging.getLogger(__name__)

TYPE_TAX_USE = [
    ('sale', 'Ventas'),
    ('purchase', 'Compras'),
    ('customer', 'Pago de Cliente'),
    ('supplier', 'Pago de Proveedor'),
    ('none', 'Ninguno'),
]

class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    type_tax_use = fields.Selection(TYPE_TAX_USE, string='Tipo de Impuesto', required=True, default="sale",
        help="Determina dónde se puede seleccionar el impuesto. Nota: 'Ninguno' significa que un impuesto no se puede usar solo, sin embargo, aún se puede usar en un grupo. 'Ajuste' se utiliza para realizar el ajuste de impuestos.")

class AccountTax(models.Model):
    _inherit = "account.tax"

    type_tax_use = fields.Selection(TYPE_TAX_USE, string='Tax Type', required=True, default="sale",
        help="Determina dónde se puede seleccionar el impuesto. Nota: 'Ninguno' significa que un impuesto no se puede usar solo, sin embargo, aún se puede usar en un grupo. 'Ajuste' se utiliza para realizar el ajuste de impuestos.")
    amount = fields.Float(string='Importe', default=0.0)
    withholding_sequence_id = fields.Many2one(
        'ir.sequence',
        'Secuencia de impuestos',
        domain=[('code', '=', 'account.tax.withholding')],
        context=(
            "{'default_code': 'account.tax.withholding',"
            " 'default_name': name}"),
        help='Si no se proporciona una secuencia, se le pedirá que ingrese el número de retención al registrar un pago.',
        copy=False
    )
    withholding_non_taxable_amount = fields.Float(
        'Monto no imponible del impuesto',
        digits=dp.get_precision('Account'),
        help="Importe a restar antes de aplicar la alícuota"
    )
    withholding_non_taxable_minimum = fields.Float(
        'Mínimo no imponible',
        digits=dp.get_precision('Account'),
        help="Importes inferiores a este no tendrán retención"
    )
    condicion_sicore = fields.Selection([
        ('withholding', 'Retencion'),
        ('perception', 'Percepcion'),
        # ('percentage_of_total', 'Percentage Of Total'),
    ],
        'Condicion de SICORE',
        help='Tipo utilizado para txt de sicore',
    )
    withholding_amount_type = fields.Selection([
        ('untaxed_amount', 'Importe neto'),
        ('total_amount', 'Importe total'),
        # ('percentage_of_total', 'Percentage Of Total'),
    ],
        'Importe base',
        help='Importe base utilizado para obtener el importe de la retención',
    )
    withholding_user_error_message = fields.Char(string='Mensaje de Error en la Retención')
    withholding_user_error_domain = fields.Char(
        string='Dominio de Error en Retención',
        default="[]",
        help='Escriba un dominio sobre el módulo de comprobante de cuenta'
    )
    withholding_advances = fields.Boolean(
        string='¿Los avances tienen retenciones?',
        default=True,
    )
    withholding_accumulated_payments = fields.Selection([
        ('month', 'Mes'),
        ('year', 'Año'),
    ],
        string='Pagos acumulados',
        help='Si no está seleccionado, entonces los pagos no son acumulables',
    )
    withholding_type = fields.Selection([
        ('none', 'None'),
        # ('percentage', 'Percentage'),
        ('based_on_rule', 'Based On Rule'),
        # ('fixed', 'Fixed Amount'),
        ('code', 'Python Code'),
        ('tabla_ganancias', 'Tabla Ganancias'),
        ('partner_tax', 'Alícuota en el Partner'),
        ('partner_iibb_padron', 'Padron en Partner'),
        # ('balance', 'Balance')
    ],
        'Tipo',
        required=True,
        default='none',
        help="El método de cálculo del importe del impuesto."
    )
    withholding_python_compute = fields.Text(
        'Python Code',
        default='''
        # withholdable_base_amount
        # payment: account.payment.group object
        # partner: res.partner object (commercial partner of payment group)
        # withholding_tax: account.tax.withholding object

        result = withholdable_base_amount * 0.10
        ''',
    )
    withholding_rule_ids = fields.One2many(
        'account.tax.withholding.rule',
        'tax_withholding_id',
        'Reglas',
    )
    amount_type = fields.Selection(default='percent', string="Tax Computation", required=True,
        selection=[('group', 'Grupo de Impuestos'), ('fixed', 'Fijo'), ('percent', 'Porcentaje'), ('division', 'Porcentaje de Impuesto sobre el Precio Incluido'), ('partner_tax', 'Alícuota en el Contacto')],
        help="""
    - Grupo de Impuestos: El impuesto es una configuración de sub-impuestos.
    - Fijo: El importe del impuesto permanece igual sea cual sea el precio .
    - Porcentaje: El importe del impuesto es un porcentaje del precio:
        ej. 100 * (1 + 10%) = 110 (precio no incluído)
        ej. 110 / (1 + 10%) = 100 (precio incluído)
    - Porcentaje de Impuesto sobre el Precio Incluido: El importe del impuesto es una división del precio:
        ej. 180 / (1 - 10%) = 200 (precio no incluído)
        ej. 200 * (1 - 10%) = 180 (precio incluído)
        """)

    def get_withholding_vals(self, payment_group, force_withholding_amount_type=None):

        commercial_partner = payment_group.commercial_partner_id

        force_withholding_amount_type = None
        if self.withholding_type == 'partner_tax':
            alicuot_line = self.get_partner_alicuot(
                commercial_partner,
                payment_group.payment_date or fields.Date.context_today(self),
            )
            alicuota = alicuot_line
        #modulo anterior account_withholding_automatic
        self.ensure_one()
        withholding_amount_type = force_withholding_amount_type or \
            self.withholding_amount_type
        withholdable_advanced_amount, withholdable_invoiced_amount = \
            payment_group._get_withholdable_amounts(
                withholding_amount_type, self.withholding_advances)

        accumulated_amount = previous_withholding_amount = 0.0

        #if self.withholding_accumulated_payments:
        #    previos_payment_groups_domain, previos_payments_domain = (
        #        self.get_period_payments_domain(payment_group))
        #    #raise ValidationError('%s %s'%(previos_payment_groups_domain, previos_payments_domain))
        #    same_period_payments = self.env['account.payment.group'].search(
        #        previos_payment_groups_domain)
        #    for same_period_payment_group in same_period_payments:
        #        same_period_amounts = \
        #            same_period_payment_group._get_withholdable_amounts(
        #                withholding_amount_type, self.withholding_advances)
        #        accumulated_amount += \
        #            same_period_amounts[0] + same_period_amounts[1]
        #    if self.withholding_type != 'tabla_ganancias':
        #        previous_withholding_amount = sum(
        #            self.env['account.payment'].search(
        #                previos_payments_domain).mapped('amount'))
        #    else:
        #        previous_withholding_amount = 0
        #        #Se cambia el dominio de busqueda payment_date a date ya que Odoo 14 descontinuo este campo en account.payment
        #        for x in range(len(previos_payments_domain)):
        #            if previos_payments_domain[x][0] == 'payment_date':
        #                l = list(previos_payments_domain[x])
        #                l[0] = 'date'
        #                previos_payments_domain[x] = tuple(l)
        #        prev_payments = self.env['account.payment'].search(previos_payments_domain)
        #        for prev_payment in prev_payments:
        #            if prev_payment.payment_group_id.payment_date.year == payment_group.payment_date.year and prev_payment.payment_group_id.payment_date.month == payment_group.payment_date.month and \
        #                    prev_payment.payment_group_id.payment_date.day <= payment_group.payment_date.day:
        #                        previous_withholding_amount += prev_payment.amount

            #raise ValidationError('%s %s'%(previous_withholding_amount,previos_payments_domain))
        total_amount = (
            accumulated_amount +
            withholdable_advanced_amount +
            withholdable_invoiced_amount)
        withholding_non_taxable_minimum = self.withholding_non_taxable_minimum
        withholding_non_taxable_amount = self.withholding_non_taxable_amount
        withholdable_base_amount = (
            (total_amount > withholding_non_taxable_minimum) and
            (total_amount - withholding_non_taxable_amount) or 0.0)
        comment = False
        if self.withholding_type == 'code':
            localdict = {
                'withholdable_base_amount': withholdable_base_amount,
                'payment': payment_group,
                'partner': payment_group.commercial_partner_id,
                'withholding_tax': self,
            }
            eval(
                self.withholding_python_compute, localdict,
                mode="exec", nocopy=True)
            period_withholding_amount = localdict['result']
        else:
            rule = self._get_rule(payment_group)
            percentage = 0.0
            fix_amount = 0.0
            if rule:
                percentage = rule.percentage
                fix_amount = rule.fix_amount
                comment = '%s x %s + %s' % (
                    withholdable_base_amount,
                    percentage,
                    fix_amount)
            if self.withholding_type != 'tabla_ganancias':
                period_withholding_amount = ((total_amount > withholding_non_taxable_minimum) and (
                    withholdable_base_amount * percentage + fix_amount) or 0.0)
            else:
                period_withholding_amount = total_amount

        vals = {
            'withholdable_invoiced_amount': withholdable_invoiced_amount,
            'withholdable_advanced_amount': withholdable_advanced_amount,
            'accumulated_amount': accumulated_amount,
            'total_amount': total_amount,
            'withholding_non_taxable_minimum': withholding_non_taxable_minimum,
            'withholding_non_taxable_amount': withholding_non_taxable_amount,
            'withholdable_base_amount': withholdable_base_amount,
            'period_withholding_amount': period_withholding_amount,
            'previous_withholding_amount': previous_withholding_amount,
            'payment_group_id': payment_group.id,
            'tax_withholding_id': self.id,
            'automatic': True,
            'comment': comment,
        }

        base_amount = vals['withholdable_base_amount']

        if self.withholding_type == 'partner_tax':
            amount = base_amount * (alicuota)
            vals['comment'] = "%s x %s" % (
                base_amount, alicuota)
            vals['period_withholding_amount'] = amount
        elif self.withholding_type == 'tabla_ganancias':
            regimen = payment_group.regimen_ganancias_id
            imp_ganancias_padron = commercial_partner.imp_ganancias_padron
            if (
                    payment_group.retencion_ganancias != 'nro_regimen' or
                    not regimen):
                amount = 0.0
            elif not imp_ganancias_padron:
                raise UserError(
                    'El contacto %s no tiene configurada inscripción en '
                    'impuesto a las ganancias' % commercial_partner.name)
            elif imp_ganancias_padron in ['EX', 'NC']:
                amount = 0.0
            elif imp_ganancias_padron == 'AC':
                if base_amount == 0:
                    base_amount = payment_group.to_pay_amount
                non_taxable_amount = (
                    regimen.montos_no_sujetos_a_retencion)
                vals['withholding_non_taxable_amount'] = non_taxable_amount
                prev_payments = []
                if self.withholding_accumulated_payments:
                    payment_date = str(payment_group.payment_date)[:8]
                    payment_date = payment_date + '00'
                    payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','=','posted'),('payment_group_id','!=',payment_group.id),\
                                        ('partner_id','=',payment_group.partner_id.id),('used_withholding','=',False),('payment_group_id.retencion_ganancias','=','nro_regimen'),'|',('tax_withholding_id.withholding_type','!=','partner_iibb_padron'),('tax_withholding_id','=',False)])
                    previous_amount = 0
                    for payment in payments:
                        if payment_group.payment_date.month == payment.payment_group_id.payment_date.month and payment_group.payment_date.year == payment.payment_group_id.payment_date.year:
                            if payment_group.payment_date.day >= payment.payment_group_id.payment_date.day:
                                if payment.payment_group_id and payment.payment_group_id.matched_move_line_ids:
                                    for matched_line in payment.payment_group_id.matched_move_line_ids:
                                        matched_amount = matched_line.move_id._get_tax_factor() * (-1) * matched_line.with_context({'payment_group_id': payment.payment_group_id.id}).payment_group_matched_amount
                                    previous_amount += matched_amount
                                else:
                                    previous_amount += payment.amount
                                prev_payments.append(str(payment.id))
                    base_amount += previous_amount
                    vals['withholdable_advanced_amount'] = previous_amount
                    payment_group.write({'temp_payment_ids': ','.join(prev_payments)})

                if base_amount < non_taxable_amount and not prev_payments:
                    base_amount = 0.0
                elif not prev_payments:
                    base_amount -= non_taxable_amount
                elif prev_payments:
                    flag_substract = True
                    for idx in prev_payments:
                        prev_pay_obj = self.env['account.payment'].browse(int(idx))
                        if prev_pay_obj.tax_withholding_id:
                            flag_substract = False
                    if flag_substract:
                        base_amount -= non_taxable_amount

                vals['withholdable_base_amount'] = base_amount
                escala = self.env['afip.tabla_ganancias.escala'].search([
                        ('importe_desde', '<=', base_amount),
                        ('importe_hasta', '>', base_amount),
                ], limit=1)
                importe_excedente = escala.importe_excedente
                #today = date.today()
                today = payment_group.payment_date
                prev_date = date(today.year,today.month,1)
                prev_payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','=','posted'),('payment_group_id.payment_date','>=',str(prev_date)),\
                                        ('payment_group_id.payment_date','<=',today),('partner_id','=',payment_group.partner_id.id),('tax_withholding_id','=',self.id)])
                if prev_payments:
                    vals['withholding_non_taxable_amount'] = 0
                    if vals['withholdable_base_amount'] == 0:
                        vals['withholdable_base_amount'] = vals['total_amount']
                    else:
                        vals['withholdable_base_amount'] = vals['withholdable_base_amount'] + payment_group.partner_id.default_regimen_ganancias_id.montos_no_sujetos_a_retencion
                    vals['period_withholding_amount'] = vals['withholdable_base_amount'] * payment_group.partner_id.default_regimen_ganancias_id.porcentaje_inscripto / 100
                    vals['previous_withholding_amount'] = 0
                    base_amount = vals['withholdable_base_amount']

                withholdable_base_amount = vals['withholdable_base_amount']
                #if not payment_group.debt_move_line_ids:
                #    withholdable_base_amount += payment_group.to_pay_amount
                #else:
                #    for matched_move in payment_group.debt_move_line_ids:
                #        matched_amount = matched_move.move_id._get_tax_factor() * (-1) * matched_move.with_context({'payment_group_id': payment_group.id}).amount_residual
                #        withholdable_base_amount += matched_amount
                
                period_withholding_amount = 0
                #non_taxable_amount = 0
                #non_taxable_amount = payment_group.partner_id.default_regimen_ganancias_id.montos_no_sujetos_a_retencion
                ## Agregar soporte a montos netos de facturas
                #prev_payments_no_withholding = self.env['account.payment'].search([('payment_type','=','outbound'),('state','=','posted'),('payment_group_id.payment_date','>=',str(prev_date)),\
                #                        ('payment_group_id.payment_date','<=',today),('partner_id','=',payment_group.partner_id.id),('tax_withholding_id','!=',self.id)])
                prev_payments_with_withholding = self.env['account.payment'].search([('payment_type','=','outbound'),('state','=','posted'),('payment_group_id.payment_date','>=',str(prev_date)),\
                                        ('payment_group_id.payment_date','<=',today),('partner_id','=',payment_group.partner_id.id),('tax_withholding_id','=',self.id)])
                #if not prev_payments_with_withholding :
                #    if prev_payments_no_withholding:
                #       for prev_payments in prev_payments_no_withholding:
                #           withholdable_base_amount += prev_payments.amount
                #    withholdable_base_amount = withholdable_base_amount - non_taxable_amount
                if withholdable_base_amount > 0:
                    period_withholding_amount = withholdable_base_amount * payment_group.partner_id.default_regimen_ganancias_id.porcentaje_inscripto / 100
                if period_withholding_amount < self.withholding_non_taxable_minimum and not prev_payments_with_withholding:
                    period_withholding_amount = 0
                vals['withholdable_base_amount'] = withholdable_base_amount
                vals['period_withholding_amount'] = period_withholding_amount
                vals['date'] = payment_group.payment_date

                if regimen.porcentaje_inscripto == -1:
                    escala = self.env['afip.tabla_ganancias.escala'].search([
                        ('importe_desde', '<=', base_amount),
                        ('importe_hasta', '>', base_amount),
                    ], limit=1)
                    if not escala:
                        raise UserError(
                            'No se encontro ninguna escala para el monto'
                            ' %s' % (base_amount))
                    amount = escala.importe_fijo

                    amount += (escala.porcentaje / 100.0) * (
                        base_amount - importe_excedente)
                    
                    vals['period_withholding_amount'] = amount

                    vals['comment'] = "%s + (%s x %s)" % (
                        escala.importe_fijo,
                        base_amount - importe_excedente,
                        escala.porcentaje / 100.0)
                else:
                    amount = period_withholding_amount
                    vals['comment'] = "%s x %s" % (
                        base_amount, regimen.porcentaje_inscripto / 100.0)
            elif imp_ganancias_padron == 'NI':
                amount = base_amount * (
                    regimen.porcentaje_no_inscripto / 100.0)
                vals['comment'] = "%s x %s" % (
                    base_amount, regimen.porcentaje_no_inscripto / 100.0)
            vals['communication'] = "%s - %s" % (
                regimen.codigo_de_regimen, regimen.concepto_referencia)
        return vals

    #def get_period_payments_domain(self, payment_group):
    #    previos_payment_groups_domain, previos_payments_domain = super(
    #        AccountTax, self).get_period_payments_domain(payment_group)
    #    if self.withholding_type == 'tabla_ganancias':
    #        previos_payment_groups_domain += [
    #            ('regimen_ganancias_id', '=',
    #                payment_group.regimen_ganancias_id.id)]
    #        previos_payments_domain += [
    #            ('payment_group_id.regimen_ganancias_id', '=',
    #                payment_group.regimen_ganancias_id.id)]
    #    return (
    #        previos_payment_groups_domain,
    #        previos_payments_domain)

    @api.model
    def create(self, vals):
        tax = super(AccountTax, self).create(vals)
        if tax.type_tax_use == 'supplier' and not tax.withholding_sequence_id:
            tax.withholding_sequence_id = self.withholding_sequence_id.\
                sudo().create({
                    'name': tax.name,
                    'implementation': 'no_gap',
                    # 'prefix': False,
                    'padding': 8,
                    'number_increment': 1,
                    'code': 'account.tax.withholding',
                    'company_id': tax.company_id.id,
                }).id
        return tax

    @api.constrains('withholding_non_taxable_amount', 'withholding_non_taxable_minimum')
    def check_withholding_non_taxable_amounts(self):
        for rec in self:
            if (
                    rec.withholding_non_taxable_amount >
                    rec.withholding_non_taxable_minimum):
                raise ValidationError(_(
                    'Non-taxable Amount can not be greater than Non-taxable '
                    'Minimum'))

    def _get_rule(self, voucher):
        self.ensure_one()
        if self.withholding_type != 'based_on_rule':
            return False
        for rule in self.withholding_rule_ids:
            try:
                domain = literal_eval(rule.domain)
            except Exception as e:
                raise ValidationError(_(
                    'Could not eval rule domain "%s".\n'
                    'This is what we get:\n%s' % (rule.domain, e)))
            domain.append(('id', '=', voucher.id))
            applies = voucher.search(domain)
            if applies:
                return rule
        return False

    def create_payment_withholdings(self, payment_group):
        for tax in self.filtered(lambda x: x.withholding_type != 'none'):
            payment_withholding = self.env[
                'account.payment'].search([
                    ('payment_group_id', '=', payment_group.id),
                    ('tax_withholding_id', '=', tax.id),
                    ('automatic', '=', True),
                ], limit=1)
            if (
                    tax.withholding_user_error_message and
                    tax.withholding_user_error_domain):
                try:
                    domain = literal_eval(tax.withholding_user_error_domain)
                except Exception as e:
                    raise ValidationError(_(
                        'Could not eval rule domain "%s".\n'
                        'This is what we get:\n%s' % (
                            tax.withholding_user_error_domain, e)))
                domain.append(('id', '=', payment_group.id))
                if payment_group.search(domain):
                    raise ValidationError(tax.withholding_user_error_message)
            vals = tax.get_withholding_vals(payment_group)
            currency = payment_group.currency_id
            period_withholding_amount = currency.round(vals.get(
                'period_withholding_amount', 0.0))
            previous_withholding_amount = currency.round(vals.get(
                'previous_withholding_amount'))
            computed_withholding_amount = max(0, (
                period_withholding_amount - previous_withholding_amount))

            if not computed_withholding_amount:
                if payment_withholding:
                    payment_withholding.unlink()
                continue

            vals['withholding_base_amount'] = vals.get(
                'withholdable_advanced_amount') + vals.get(
                'withholdable_invoiced_amount')
            vals['amount'] = computed_withholding_amount
            vals['computed_withholding_amount'] = computed_withholding_amount

            vals.pop('comment')
            if payment_withholding:
                #payment_withholding.write(vals)
                payment_withholding.unlink()
            
            payment_method = self.env.ref(
                'l10n_ar_withholding.'
                'account_payment_method_out_withholding')
            journal = self.env['account.journal'].search([
                ('company_id', '=', tax.company_id.id),
                ('outbound_payment_method_line_ids.payment_method_id', '=', payment_method.id),
                ('type', 'in', ['cash', 'bank']),
            ], limit=1)
            if not journal:
                raise UserError(_(
                    'No journal for withholdings found on company %s') % (
                    tax.company_id.name))
            vals['journal_id'] = journal.id
            vals['payment_method_id'] = payment_method.id
            vals['payment_type'] = 'outbound'
            vals['partner_type'] = payment_group.partner_type
            vals['partner_id'] = payment_group.partner_id.id
            #if not 'name' in vals:
            #    sequence_obj = self.env['ir.sequence']
            #    correlativo = sequence_obj.next_by_code('account.tax.withholding')
            #    vals['name'] = correlativo
            payment_withholding = payment_withholding.create(vals)
        return True

    def get_period_payments_domain(self, payment_group):
        """
        We make this here so it can be inherited by localizations
        """
        to_date = fields.Date.from_string(
            payment_group.payment_date) or datetime.date.today()
        common_previous_domain = [
            ('partner_id.commercial_partner_id', '=',
                payment_group.commercial_partner_id.id),
        ]
        if self.withholding_accumulated_payments == 'month':
            from_relative_delta = relativedelta(day=1)
        elif self.withholding_accumulated_payments == 'year':
            from_relative_delta = relativedelta(day=1, month=1)
        from_date = to_date + from_relative_delta
        common_previous_domain += [
            ('payment_date', '<=', to_date),
            ('payment_date', '>=', from_date),
        ]

        previous_payment_groups_domain = [
            ('payment_date', '<=', to_date),
            ('payment_date', '>=', from_date),
            ('state', 'not in', ['draft', 'cancel', 'confirmed']),
            ('id', '!=', payment_group.id),
        ]

        previous_payments_domain = common_previous_domain + [
            ('payment_group_id.state', 'not in',
                ['draft', 'cancel', 'confirmed']),
            ('state', '!=', 'cancel'),
            ('tax_withholding_id', '=', self.id),
            ('payment_group_id.id', '!=', payment_group.id),
        ]
        if self.withholding_type == 'tabla_ganancias':
            previous_payment_groups_domain += [
                ('regimen_ganancias_id', '=',
                    payment_group.regimen_ganancias_id.id),
                ('receiptbook_id.partner_type','=','supplier'),
                ('partner_id', '=', payment_group.partner_id.id)]
            previous_payments_domain += [
                ('payment_group_id.regimen_ganancias_id', '=',
                    payment_group.regimen_ganancias_id.id),
                ('partner_id', '=', payment_group.partner_id.id)]
        return (previous_payment_groups_domain, previous_payments_domain)

    #def get_partner_alicuota_percepcion(self, partner, date):
    #    if partner and date:
    #        arba = self.get_partner_alicuot(partner, date)
    #        return arba.alicuota_percepcion / 100.0
    #    return 0.0
#
    #def get_partner_alicuot(self, partner, date):
    #    self.ensure_one()
    #    commercial_partner = partner.commercial_partner_id
    #    company = self.company_id
    #    alicuot = 0
    #    for alicuot_id in commercial_partner.arba_alicuot_ids:
    #        if alicuot_id.tax_id.id == self.id:
    #            alicuot = alicuot_id.percent
    #    return alicuot

    def _compute_amount(
            self, base_amount, price_unit, quantity=1.0, product=None,
            partner=None):
        if self.amount_type == 'partner_tax':
            # TODO obtener fecha de otra manera?
            try:
                date = self._context.date_invoice
            except Exception:
                date = fields.Date.context_today(self)
            return base_amount * self.get_partner_alicuota_percepcion(
                partner, date)
        else:
            return super(AccountTax, self)._compute_amount(
                base_amount, price_unit, quantity, product, partner)
