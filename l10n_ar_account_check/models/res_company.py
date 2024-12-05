from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

class ResCompany(models.Model):
    _inherit = 'res.company'

    rejected_check_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Cheques Rechazados',
        help='Cuenta para Cheques Rechazados, por ejemplo "Cheques Rechazados"',
    )
    deferred_check_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Cheques Diferidos',
        help='Cuenta para Cheques Diferidos, por ejemplo "Cheques Diferidos"',
    )
    holding_check_account_id = fields.Many2one(
        'account.account',
        'Cuenta de Cheques Propios',
        help='Cuenta para Cheques Propios, por ejemplo "Cheques Propios"',
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
            raise UserError(_("El tipo de Cheque %s no está implementado") % check_type)
        if not account:
            raise UserError(_(
                'No hay cuenta de cheque %s definida para la compañía %s'
            ) % (check_type, self.name))
        return account
