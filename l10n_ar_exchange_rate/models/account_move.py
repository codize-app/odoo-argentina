from odoo import api, fields, models, _, Command, SUPERUSER_ID
from contextlib import ExitStack, contextmanager
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from odoo.tools import (
    create_index,
    date_utils,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    groupby,
    index_exists,
    OrderedSet,
    SQL,

import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

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
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        with self._disable_recursion(container, 'check_move_validity', default=True, target=False) as disabled:
            yield
            if disabled:
                return
        for move in self:
            if move.l10n_ar_is_manual_rate:
                return

        if unbalanced_moves := self._get_unbalanced_moves(container):
            if len(unbalanced_moves) == 1:
                raise UserError("El apunte no está balanceado.")

            error_msg = _("El movimiento está desbalanceado:\n\n")
            for move in unbalanced_moves:
                error_msg += f"  - {self.browse(move[0]).name}\n"

            raise UserError(error_msg)

    l10n_ar_manual_currency_rate = fields.Float(string='Tasa de cambio manual', readonly=False, compute='_get_currency_rate', store=True)
    l10n_ar_is_manual_rate = fields.Boolean(string='Usar TC manual')
