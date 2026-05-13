from odoo import api, fields, models, _
from contextlib import contextmanager
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_ar_manual_currency_rate = fields.Float(
        string='Tasa de cambio manual',
        compute='_compute_currency_rate',
        store=True,
        readonly=False
    )

    l10n_ar_is_manual_rate = fields.Boolean(
        string='Usar TC manual'
    )

    # =========================
    # COMPUTE
    # =========================
    @api.depends('currency_id', 'l10n_ar_is_manual_rate')
    def _compute_currency_rate(self):
        for record in self:
            rate = 1.0

            if not record.l10n_ar_is_manual_rate:
                if record.currency_id and record.currency_id.rate > 0:
                    if record.currency_id.name != 'ARS':
                        rate = 1 / record.currency_id.rate

            record.l10n_ar_manual_currency_rate = rate

    # =========================
    # LOGICA MANUAL
    # =========================
    def l10n_ar_manual_rate(self):
        for move in self:
            if not move.l10n_ar_is_manual_rate:
                continue

            for line in move.line_ids:
                if line.debit > 0:
                    line.debit = abs(line.amount_currency) * move.l10n_ar_manual_currency_rate
                elif line.credit > 0:
                    line.credit = abs(line.amount_currency) * move.l10n_ar_manual_currency_rate

    # =========================
    # VALIDACION BALANCE
    # =========================
    @contextmanager
    def _check_balanced(self, container):
        with self._disable_recursion(container, 'check_move_validity', default=True, target=False) as disabled:
            yield
            if disabled:
                return

        moves_to_check = self.filtered(lambda m: not m.l10n_ar_is_manual_rate)

        if not moves_to_check:
            return

        unbalanced_moves = moves_to_check._get_unbalanced_moves(container)

        if unbalanced_moves:
            if len(unbalanced_moves) == 1:
                raise UserError("El apunte no está balanceado.")

            error_msg = _("El movimiento está desbalanceado:\n\n")
            for move in unbalanced_moves:
                error_msg += f"  - {self.browse(move[0]).name}\n"

            raise UserError(error_msg)