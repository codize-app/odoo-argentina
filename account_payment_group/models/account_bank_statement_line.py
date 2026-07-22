from odoo import models

# Note: In Odoo 17+, account.bank.statement.line no longer has
# button_cancel_reconciliation or process_reconciliation methods.
# Bank statement reconciliation is handled differently via account.move.
# Payment group cancellation is handled through the payment group's
# own cancel/unlink flow triggered by action_cancel on related payments.


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
