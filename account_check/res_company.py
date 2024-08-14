from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    rejected_check_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Cheques Rechazados',
        help='Cuenta de Cheques Rechazados, por ejemplo "Cheques Rechazados"',
    )
    deferred_check_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Cheques Diferidos',
        help='Cuenta de Cheques Diferidos, for eg. "Deferred Checks"',
    )
    holding_check_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Cheques en Tenencia',
        help='Cuenta de Cheques en Tenencia para cheques de terceros, por ejemplo "Cheques en Tenencia"',
    )

    def _get_check_account(self, check_type):
        self.ensure_one()
        if check_type == 'holding':
            account = self.holding_check_account_id
        elif check_type == 'rejected':
            account = self.rejected_check_account_id
        elif check_type == 'deferred':
            account = self.deferred_check_account_id
        else:
            raise UserError(_("¡El tipo de cheque %s no está implementado!") % check_type)
        if not account:
            raise UserError(_(
                'No hay cuenta de cheques %s definida para la compañía %s'
            ) % (check_type, self.name))
        return account
