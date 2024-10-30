from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    rejected_check_id = fields.Many2one(
        'account.check',
        'Cheque Rechazado',
    )

    def action_cancel(self):
        """
        Si al cancelar la factura la misma estaba vinculada a un rechazo
        intentamos romper la conciliacion del rechazo
        """
        for rec in self.filtered(lambda x: x.rejected_check_id):
            check = rec.rejected_check_id
            deferred_account = check.company_id._get_check_account('deferred')
            if (
                    check.state == 'rejected' and
                    check.type == 'issue_check' and
                    deferred_account.reconcile):
                deferred_account_line = rec.move_id.line_ids.filtered(
                    lambda x: x.account_id == deferred_account)
                deferred_account_line.remove_move_reconcile()
        return super(AccountMove, self).action_cancel()
