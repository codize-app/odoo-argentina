# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta
import datetime
from datetime import date


class AccountTax(models.Model):
    _inherit = "account.tax"

    amount_type = fields.Selection(default='percent', string="Tax Computation", required=True,
        selection=[('group', 'Group of Taxes'), ('fixed', 'Fixed'), ('percent', 'Percentage of Price'), ('division', 'Percentage of Price Tax Included'),('partner_tax','Alicuota en el partner')],
        help="""
    - Group of Taxes: The tax is a set of sub taxes.
    - Fixed: The tax amount stays the same whatever the price.
    - Percentage of Price: The tax amount is a % of the price:
        e.g 100 * (1 + 10%) = 110 (not price included)
        e.g 110 / (1 + 10%) = 100 (price included)
    - Percentage of Price Tax Included: The tax amount is a division of the price:
        e.g 180 / (1 - 10%) = 200 (not price included)
        e.g 200 * (1 - 10%) = 180 (price included)
        """)

    def get_period_payments_domain(self, payment_group):
        previos_payment_groups_domain, previos_payments_domain = super(
            AccountTax, self).get_period_payments_domain(payment_group)
        if self.withholding_type == 'tabla_ganancias':
            previos_payment_groups_domain += [
                ('regimen_ganancias_id', '=',
                    payment_group.regimen_ganancias_id.id)]
            previos_payments_domain += [
                ('payment_group_id.regimen_ganancias_id', '=',
                    payment_group.regimen_ganancias_id.id)]
        return (
            previos_payment_groups_domain,
            previos_payments_domain)

    def get_withholding_vals(self, payment_group):
        commercial_partner = payment_group.commercial_partner_id

        force_withholding_amount_type = None
        if self.withholding_type == 'partner_tax':
            alicuot_line = self.get_partner_alicuot(
                commercial_partner,
                payment_group.payment_date or fields.Date.context_today(self),
            )
            alicuota = alicuot_line

        vals = super(AccountTax, self).get_withholding_vals(
            payment_group, force_withholding_amount_type)
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
                # if amount zero then we dont create withholding
                amount = 0.0
            elif not imp_ganancias_padron:
                raise UserError(
                    'El partner %s no tiene configurada inscripcion en '
                    'impuesto a las ganancias' % commercial_partner.name)
            elif imp_ganancias_padron in ['EX', 'NC']:
                # if amount zero then we dont create withholding
                amount = 0.0
            # TODO validar excencion actualizada
            elif imp_ganancias_padron == 'AC':
                if base_amount == 0:
                    base_amount = payment_group.to_pay_amount
                # alicuota inscripto
                non_taxable_amount = (
                    regimen.montos_no_sujetos_a_retencion)
                vals['withholding_non_taxable_amount'] = non_taxable_amount
                prev_payments = []
                if self.withholding_accumulated_payments:
                    payment_date = str(payment_group.payment_date)[:8]
                    payment_date = payment_date + '00'
                    payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','=','posted'),('payment_group_id','!=',payment_group.id),\
                                        ('partner_id','=',payment_group.partner_id.id),('used_withholding','=',False),('payment_group_id.retencion_ganancias','=','nro_regimen')])
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
                                    # esta linea MGO
                                prev_payments.append(str(payment.id))
                    base_amount += previous_amount
                    payment_group.write({'temp_payment_ids': ','.join(prev_payments)})

                if base_amount < non_taxable_amount and not prev_payments:
                    base_amount = 0.0
                elif not prev_payments:
                    #raise ValidationError('estamos aca #2')
                    base_amount -= non_taxable_amount
                elif prev_payments:
                    flag_substract = True
                    for idx in prev_payments:
                        prev_pay_obj = self.env['account.payment'].browse(int(idx))
                        if prev_pay_obj.tax_withholding_id:
                            flag_substract = False
                    if flag_substract:
                        #raise ValidationError('estamos aca #3')
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
                #raise ValidationError('estamos aca %s %s'%(prev_payments,vals))

                # Changes MGO - base imponible
                withholdable_base_amount = 0
                if not payment_group.debt_move_line_ids:
                    withholdable_base_amount += payment_group.to_pay_amount
                else:
                    for matched_move in payment_group.debt_move_line_ids:
                        matched_amount = matched_move.move_id._get_tax_factor() * (-1) * matched_move.with_context({'payment_group_id': payment_group.id}).amount_residual
                        withholdable_base_amount += matched_amount
                #raise ValidationError('estamos aca %s'%(withholdable_base_amount))
                period_withholding_amount = 0
                non_taxable_amount = 0
                non_taxable_amount = payment_group.partner_id.default_regimen_ganancias_id.montos_no_sujetos_a_retencion
                # Agregar soporte a montos netos de facturas
                prev_payments_no_withholding = self.env['account.payment'].search([('payment_type','=','outbound'),('state','=','posted'),('payment_group_id.payment_date','>=',str(prev_date)),\
                                        ('payment_group_id.payment_date','<=',today),('partner_id','=',payment_group.partner_id.id),('tax_withholding_id','!=',self.id)])
                prev_payments_with_withholding = self.env['account.payment'].search([('payment_type','=','outbound'),('state','=','posted'),('payment_group_id.payment_date','>=',str(prev_date)),\
                                        ('payment_group_id.payment_date','<=',today),('partner_id','=',payment_group.partner_id.id),('tax_withholding_id','=',self.id)])
                if not prev_payments_with_withholding :
                    if prev_payments_no_withholding:
                        for prev_payments in prev_payments_no_withholding:
                            withholdable_base_amount += prev_payments.amount
                    withholdable_base_amount = withholdable_base_amount - non_taxable_amount
                if withholdable_base_amount > 0:
                    period_withholding_amount = withholdable_base_amount * payment_group.partner_id.default_regimen_ganancias_id.porcentaje_inscripto / 100
                if period_withholding_amount < self.withholding_non_taxable_minimum and not prev_payments_with_withholding:
                    period_withholding_amount = 0
                vals['withholdable_base_amount'] = withholdable_base_amount
                vals['period_withholding_amount'] = period_withholding_amount



                if regimen.porcentaje_inscripto == -1:
                    # hacemos <= porque si es 0 necesitamos que encuentre
                    # la primer regla (0 es en el caso en que la no
                    # imponible sea mayor)
                    escala = self.env['afip.tabla_ganancias.escala'].search([
                        ('importe_desde', '<=', base_amount),
                        ('importe_hasta', '>', base_amount),
                    ], limit=1)
                    if not escala:
                        raise UserError(
                            'No se encontro ninguna escala para el monto'
                            ' %s' % (base_amount))
                    amount = escala.importe_fijo
                    #amount += (escala.porcentaje / 100.0) * (
                    #    base_amount - escala.importe_excedente)
                    amount += (escala.porcentaje / 100.0) * (
                        base_amount - importe_excedente)
                    #vals['comment'] = "%s + (%s x %s)" % (
                    #    escala.importe_fijo,
                    #    base_amount - escala.importe_excedente,
                    #    escala.porcentaje / 100.0)
                    vals['comment'] = "%s + (%s x %s)" % (
                        escala.importe_fijo,
                        base_amount - importe_excedente,
                        escala.porcentaje / 100.0)
                else:
                    # raise ValidationError('llegamos aca')
                    #amount = base_amount * (
                    #    regimen.porcentaje_inscripto / 100.0)
                    amount = period_withholding_amount
                    vals['comment'] = "%s x %s" % (
                        base_amount, regimen.porcentaje_inscripto / 100.0)
            elif imp_ganancias_padron == 'NI':
                # alicuota no inscripto
                amount = base_amount * (
                    regimen.porcentaje_no_inscripto / 100.0)
                vals['comment'] = "%s x %s" % (
                    base_amount, regimen.porcentaje_no_inscripto / 100.0)
            # TODO, tal vez sea mejor utilizar otro campo?
            vals['communication'] = "%s - %s" % (
                regimen.codigo_de_regimen, regimen.concepto_referencia)
            #if amount < self.withholding_non_taxable_minimum:
            #    amount = 0

            # vals['period_withholding_amount'] = amount
        # raise ValidationError('estamos aca %s'%(vals))
        return vals

    def get_partner_alicuota_percepcion(self, partner, date):
        if partner and date:
            arba = self.get_partner_alicuot(partner, date)
            return arba.alicuota_percepcion / 100.0
        return 0.0

    def get_partner_alicuot(self, partner, date):
        self.ensure_one()
        commercial_partner = partner.commercial_partner_id
        company = self.company_id
        alicuot = 0
        for alicuot_id in commercial_partner.arba_alicuot_ids:
            if alicuot_id.tax_id.id == self.id:
                alicuot = alicuot_id.percent
        return alicuot

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
