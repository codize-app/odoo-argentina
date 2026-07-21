# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends('state', 'tax_withholding_id')
    def _compute_print_withholding(self):
        for rec in self:
            rec.print_withholding = rec.state == 'posted' and bool(rec.tax_withholding_id)

    tax_withholding_id = fields.Many2one(
        'account.tax',
        string='Impuesto de retención',
    )
    withholding_number = fields.Char(
        help="Si no configura un número agregaremos un número automáticamente "
        "a partir de una secuencia que debe ser configurada en el Impuesto de Retención"
    )
    withholding_base_amount = fields.Monetary(
        string='Monto base de retención',
    )
    communication = fields.Text('Notas')
    automatic = fields.Boolean()
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
    accumulated_amount = fields.Float('Monto acumulado', readonly=True)
    total_amount = fields.Float('Monto total', readonly=True)
    withholding_non_taxable_minimum = fields.Float(
        'Mínimo no imponible',
        readonly=True,
    )
    withholding_non_taxable_amount = fields.Float(
        'Monto no imponible',
        readonly=True,
    )
    withholdable_base_amount = fields.Float('Monto base sujeto a retención', readonly=True)
    period_withholding_amount = fields.Float('Retención del período')
    previous_withholding_amount = fields.Float('Retención período anterior', readonly=True)
    computed_withholding_amount = fields.Float('Retención calculada')
    used_withholding = fields.Boolean(string='Usado en retenciones')
    print_withholding = fields.Boolean(
        'Imprimir Retenciones',
        compute='_compute_print_withholding',
        store=False,
    )

    def btn_print_withholding(self):
        self.ensure_one()
        return self.env.ref('l10n_ar_withholding_automatic.account_payment_withholdings').report_action(self)

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
            if payment.name == '/':
                payment.write({'name': payment.withholding_number})

        return super().action_post()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        res = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals, force_balance=force_balance)
        if self.tax_withholding_id and res:
            account_imp_ret = self.tax_withholding_id.invoice_repartition_line_ids.filtered(
                lambda r: r.account_id)
            if account_imp_ret:
                _logger.info(
                    "[RET] Forzando cuenta %s en pago %s (antes: %s)",
                    account_imp_ret[0].account_id.display_name, self.id, res[0].get('account_id'))
                res[0]['account_id'] = account_imp_ret[0].account_id.id
        return res

    def _compute_payment_method_description(self):
        payments = self.filtered(
            lambda x: x.payment_method_code == 'withholding')
        for rec in payments:
            name = rec.tax_withholding_id.name or rec.payment_method_id.name
            rec.payment_method_description = name
        return super(
            AccountPayment,
            (self - payments))._compute_payment_method_description()
