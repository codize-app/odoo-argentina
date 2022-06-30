# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class AccountPaymentGroupInherit(models.Model):
    _inherit = "account.payment.group"

    def compute_withholdings(self):
        res = super(AccountPaymentGroupInherit, self).compute_withholdings()
        for rec in self:
            # Verificamos por Retenciones de IIBB en el proveedor
            if len(rec.partner_id.alicuot_ret_arba_ids) > 0:
                retencion = rec.partner_id.alicuot_ret_arba_ids.filtered(lambda l: l.padron_activo == True)[0]

                amount_untaxed_total_invs = 0
                for invs in self.debt_move_line_ids:
                    amount_untaxed_total_invs += invs.move_id.amount_untaxed
                _amount_ret_iibb = amount_untaxed_total_invs * (retencion.a_ret / 100)
                _payment_method = self.env.ref(
                    'l10n_ar_withholding.'
                    'account_payment_method_out_withholding')
                _journal = self.env['account.journal'].search([
                    ('company_id', '=', rec.company_id.id),
                    ('outbound_payment_method_ids', '=', _payment_method.id),
                    ('type', 'in', ['cash', 'bank']),
                ], limit=1)
                _imp_ret = self.env['account.tax'].search([
                    ('type_tax_use', '=', rec.partner_type),
                    ('company_id', '=', rec.company_id.id),
                    ('withholding_type', '=', 'partner_iibb_padron'),
                    ('tax_arba_ret','=',True)], limit=1)
                rec.payment_ids = [(0,0, {
                    'name': '/',
                    'payment_type': 'outbound',
                    'journal_id': _journal.id,
                    'tax_withholding_id': _imp_ret.id,
                    'payment_method_description': 'Retencion IIBB',
                    'payment_method_id': _payment_method.id,
                    'date': rec.payment_date,
                    'destination_account_id': rec.partner_id.property_account_payable_id.id,
                    'amount': _amount_ret_iibb,
                    'withholding_base_amount': amount_untaxed_total_invs
                })]

                # Busco en las lineas de pago cual es el pago de retencion para luego cambiarle en su asiento contable la cuenta, 
                # esto lo hacemos porque por defecto toma la cuenta del diario y queremos que tome la cuenta configurada en el impuesto
                line_ret = rec.payment_ids.filtered(lambda r: r.tax_withholding_id.id == _imp_ret.id)
                line_tax_account = line_ret.move_id.line_ids.filtered(lambda r: r.credit > 0)
                account_imp_ret = _imp_ret.invoice_repartition_line_ids.filtered(lambda r: len(r.account_id) > 0)
                if len(account_imp_ret) > 0:
                    #Guardo "Cuenta de efectivo" que tiene el diario
                    cuenta_anterior = line_ret.move_id.journal_id.default_account_id
                    #La cambio por la cuenta que tiene el impuesto de retencion configurada
                    line_ret.move_id.journal_id.default_account_id = account_imp_ret.account_id
                    #Cambio en el Apunte contable del Asiento contable la cuenta que esta configurada en el impuesto de retencion
                    line_tax_account.account_id = account_imp_ret.account_id
                    #Vuelvo a poner en el diario la cuenta que tenia anteriormente
                    line_ret.move_id.journal_id.default_account_id = cuenta_anterior
                    #TODO Este cambio se hace para evitar el error de validacion que hace por defecto en
                    #https://github.com/odoo/odoo/blob/14.0/addons/account/models/account_payment.py#L699
                    #Es necesario revisar si este funcionamiento es correcto o existe una forma diferente de realizar

        return res