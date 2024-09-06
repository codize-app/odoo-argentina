from odoo import api, fields, models, _, Command, SUPERUSER_ID
from contextlib import ExitStack, contextmanager
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from odoo.tools import (
    date_utils,
    email_re,
    email_split,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    groupby,
    is_html_empty,
    sql
)
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, values):
        res = super(AccountMove, self).write(values)
        for rec in self:
            rec.sudo().with_context(check_move_validity=False, check_amount_currency_balance_sign=False).l10n_ar_manual_rate()
        return res

    @api.model
    def create(self, values):
        res = super(AccountMove, self).create(values)
        for rec in self:
            rec.sudo().with_context(check_move_validity=False, check_amount_currency_balance_sign=False).l10n_ar_manual_rate()
        return res

    def l10n_ar_manual_rate(self):
        for line in self.line_ids:
            if self.l10n_ar_is_manual_rate == True:
                if line.debit > 0:
                    line.debit = abs(line.amount_currency) * self.l10n_ar_manual_currency_rate
                if line.credit > 0:
                    line.credit = abs(line.amount_currency) * self.l10n_ar_manual_currency_rate

    @api.depends('currency_id')
    def _get_currency_rate(self):
        for record in self:
            rate = 1
            if record.l10n_ar_is_manual_rate == False:
                if record.currency_id.rate > 0:
                    if record.currency_id.name != 'ARS':
                        rate = 1 / record.currency_id.rate
                    else:
                        rate = 1
                    record.l10n_ar_manual_currency_rate = rate

    @contextmanager
    def _check_balanced(self, container):
        with self._disable_recursion(container, 'check_move_validity', default=True, target=False) as disabled:
            yield
            if disabled:
                return

        for move in self:
            if move.l10n_ar_is_manual_rate:
                return True

        unbalanced_moves = self._get_unbalanced_moves(container)
        if unbalanced_moves:
            error_msg = "Ocurrió un error."
            for move_id, sum_debit, sum_credit in unbalanced_moves:
                move = self.browse(move_id)
                error_msg += _(
                    "\n\n"
                    "El movimiento (%s) no está balanceado.\n"
                    "El total de débito es %s y el total de crédito es %s.\n"
                    "Posiblemente quiera especificar una cuenta por defecto en el diario \"%s\" para balancear el movimiento automáticamente.",
                    move.display_name,
                    format_amount(self.env, sum_debit, move.company_id.currency_id),
                    format_amount(self.env, sum_credit, move.company_id.currency_id),
                    move.journal_id.name)
            raise UserError(error_msg)

    l10n_ar_manual_currency_rate = fields.Float(string='Tasa de cambio manual', readonly=False, compute='_get_currency_rate', store=True)
    l10n_ar_is_manual_rate = fields.Boolean(string='Usar TC manual')
