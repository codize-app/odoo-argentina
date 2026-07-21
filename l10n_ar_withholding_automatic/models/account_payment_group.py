# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class AccountPaymentGroup(models.Model):
    _inherit = "account.payment.group"

    withholdings_amount = fields.Monetary(
        compute='_compute_withholdings_amount'
    )
    withholdable_advanced_amount = fields.Monetary(
        'Ajustes / Avance (sin impuestos)',
        help='A veces se utiliza para el cálculo de retenciones',
    )
    withholdable_advanced_amount_calculation_type = fields.Selection([
        ('iva21', 'IVA 21%'),
        ('iva10', 'IVA 10,5%'),
        ('none', 'Ninguna'),
    ], 'Deduccion de total a pagar',
        help='Este campo se utiliza para pagos adelantados, el cual selecciona el tipo de deduccion '
             'que se le hara al total del pago para luego hacer el calculo de retencion. '
             'Solo aplicable cuando el pago no tiene una o varias facturas asociadas',
        default='iva21'
    )
    retencion_ganancias = fields.Selection([
        ('imposibilidad_retencion', 'Imposibilidad de Retención'),
        ('no_aplica', 'No Aplica'),
        ('nro_regimen', 'Nro de Régimen'),
    ],
        'Retención Ganancias',
    )
    regimen_ganancias_id = fields.Many2one(
        'afip.tabla_ganancias.alicuotasymontos',
        'Régimen Ganancias',
        ondelete='restrict',
    )
    company_regimenes_ganancias_ids = fields.Many2many(
        'afip.tabla_ganancias.alicuotasymontos',
        compute='_company_regimenes_ganancias',
    )
    temp_payment_ids = fields.Char('temp_payment_ids')

    @api.onchange('unreconciled_amount', 'withholdable_advanced_amount_calculation_type')
    def set_withholdable_advanced_amount(self):
        for rec in self:
            if rec.withholdable_advanced_amount_calculation_type == 'iva21':
                rec.withholdable_advanced_amount = (rec.unreconciled_amount / 1.21)
            elif rec.withholdable_advanced_amount_calculation_type == 'iva10':
                rec.withholdable_advanced_amount = (rec.unreconciled_amount / 1.105)
            else:
                rec.withholdable_advanced_amount = rec.unreconciled_amount

    @api.depends(
        'payment_ids.tax_withholding_id',
        'payment_ids.amount',
    )
    def _compute_withholdings_amount(self):
        for rec in self:
            rec.withholdings_amount = sum(
                rec.payment_ids.filtered(
                    lambda x: x.tax_withholding_id).mapped('amount'))

    def compute_withholdings(self):
        for rec in self:
            if rec.partner_type != 'supplier':
                continue

            if rec.commercial_partner_id.imp_ganancias_padron in ['EX', 'NC']:
                rec.retencion_ganancias = 'no_aplica'
                continue
            else:
                cia_regs = rec.company_regimenes_ganancias_ids
                partner_regimen = (
                    rec.commercial_partner_id.default_regimen_ganancias_id)
                if partner_regimen:
                    def_regimen = partner_regimen
                elif cia_regs:
                    def_regimen = cia_regs[0]
                else:
                    def_regimen = False
                rec.retencion_ganancias = 'nro_regimen'
                rec.regimen_ganancias_id = def_regimen

            self.env['account.tax'].with_context(type=None).search([
                ('type_tax_use', '=', rec.partner_type),
                ('company_id', '=', rec.company_id.id),
            ]).create_payment_withholdings(rec)

            _imp_ret_ganancias = self.env['account.tax'].search(
                [('withholding_type', '=', 'tabla_ganancias')], limit=1)
            line_ret = rec.payment_ids.filtered(
                lambda r: r.tax_withholding_id.id == _imp_ret_ganancias.id)
            line_tax_account = line_ret.move_id.line_ids.filtered(
                lambda r: r.credit > 0)
            account_imp_ret = _imp_ret_ganancias.invoice_repartition_line_ids.filtered(
                lambda r: len(r.account_id) > 0)
            if len(account_imp_ret) > 0:
                cuenta_anterior = line_ret.move_id.journal_id.default_account_id
                line_ret.move_id.journal_id.default_account_id = account_imp_ret.account_id
                line_tax_account.account_id = account_imp_ret.account_id
                line_ret.move_id.journal_id.default_account_id = cuenta_anterior

    def confirm(self):
        res = super().confirm()
        for rec in self:
            if rec.company_id.automatic_withholdings:
                rec.compute_withholdings()
        return res

    def _get_withholdable_amounts(self, withholding_amount_type, withholding_advances):
        """Method to help on getting withholding amounts from account.tax"""
        self.ensure_one()
        if self.state == 'posted':
            untaxed_field = 'matched_amount_untaxed'
            total_field = 'matched_amount'
        else:
            untaxed_field = 'selected_debt_untaxed'
            total_field = 'selected_debt'

        if withholding_amount_type == 'untaxed_amount':
            withholdable_invoiced_amount = self[untaxed_field]
        else:
            withholdable_invoiced_amount = self[total_field]

        withholdable_advanced_amount = 0.0

        if self.withholdable_advanced_amount < 0.0 and \
                self.to_pay_move_line_ids and self.state != 'posted':
            withholdable_advanced_amount = 0.0

            sign = self.partner_type == 'supplier' and -1.0 or 1.0
            sorted_to_pay_lines = sorted(
                self.to_pay_move_line_ids,
                key=lambda a: a.date_maturity or a.date)

            partial_line = sorted_to_pay_lines[-1]
            if sign * partial_line.amount_residual < \
                    sign * self.withholdable_advanced_amount:
                raise ValidationError(_(
                    'Seleccionó deuda por %s pero aparentente desea pagar '
                    ' %s. En la deuda seleccionada hay algunos comprobantes de'
                    ' mas que no van a poder ser pagados (%s). Deberá quitar '
                    ' dichos comprobantes de la deuda seleccionada para poder '
                    'hacer el correcto cálculo de las retenciones.' % (
                        self.selected_debt,
                        self.to_pay_amount,
                        partial_line.move_id.display_name,
                        )))

            if withholding_amount_type == 'untaxed_amount' and \
                    partial_line.move_id:
                invoice_factor = partial_line.move_id._get_tax_factor()
            else:
                invoice_factor = 1.0

            withholdable_invoiced_amount -= (
                sign * self.unreconciled_amount * invoice_factor)
        elif withholding_advances:
            if self.state == 'posted':
                if self.unreconciled_amount and \
                   self.withholdable_advanced_amount:
                    withholdable_advanced_amount = self.unmatched_amount * (
                        self.withholdable_advanced_amount /
                        self.unreconciled_amount)
                else:
                    withholdable_advanced_amount = self.unmatched_amount
            else:
                withholdable_advanced_amount = \
                    self.withholdable_advanced_amount
        return (withholdable_advanced_amount, withholdable_invoiced_amount)

    def _company_regimenes_ganancias(self):
        for rec in self.filtered(lambda x: x.partner_type == 'supplier'):
            rec.company_regimenes_ganancias_ids = (
                rec.company_id.regimenes_ganancias_ids)
        for rec in self.filtered(lambda x: x.partner_type == 'customer'):
            rec.company_regimenes_ganancias_ids = [fields.Command.clear()]

    @api.onchange('commercial_partner_id')
    def change_retencion_ganancias(self):
        if not self.commercial_partner_id:
            self.retencion_ganancias = False
            self.regimen_ganancias_id = False
            return
        if self.commercial_partner_id.imp_ganancias_padron in ['EX', 'NC']:
            self.retencion_ganancias = 'no_aplica'
        else:
            partner_regimen = (
                self.commercial_partner_id.default_regimen_ganancias_id)
            if partner_regimen:
                def_regimen = partner_regimen
            else:
                # Solo leer el campo computado si el registro ya existe en BD
                if self._origin and self._origin.id:
                    cia_regs = self.company_regimenes_ganancias_ids
                    def_regimen = cia_regs[0] if cia_regs else False
                else:
                    def_regimen = False
            self.regimen_ganancias_id = def_regimen

    @api.onchange('company_regimenes_ganancias_ids')
    def change_company_regimenes_ganancias(self):
        if self.company_regimenes_ganancias_ids:
            self.retencion_ganancias = 'nro_regimen'

    def post(self):
        res = super().post()
        for rec in self:
            if rec.temp_payment_ids:
                payment_ids = rec.temp_payment_ids.split(',')
                for payment_id in payment_ids:
                    payment = self.env['account.payment'].browse(int(payment_id))
                    _logger.warning('**** Entro aqui con pago: {}'.format(payment))
                    if payment.tax_withholding_id.withholding_type != 'partner_iibb_padron':
                        _logger.warning('**** Actualizo pago: {}'.format(payment))
                        payment.write({'used_withholding': True})

            withholding = None
            for payment in rec.payment_ids:
                if payment.tax_withholding_id and payment.tax_withholding_id.withholding_type != 'partner_iibb_padron':
                    withholding = True
            if withholding:
                for payment in rec.payment_ids:
                    if payment.tax_withholding_id.withholding_type != 'partner_iibb_padron':
                        payment.write({'used_withholding': True})

        return res
